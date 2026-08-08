from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import Organization, AgentOrganizationMapping

User = get_user_model()


# ---------------------------------------------------------------------
# Small helper functions (permission checks)
# ---------------------------------------------------------------------

def organization_list(request):
    return render(request, "Agent/organization_list.html")


def _get_membership(agent, organization_id):
    """Return the logged-in agent's ACTIVE mapping row for an org, or None."""
    return AgentOrganizationMapping.objects.filter(
        agent=agent,
        organization_id=organization_id,
        status=AgentOrganizationMapping.Status.ACTIVE,
    ).first()


def _is_owner(agent, organization_id):
    membership = _get_membership(agent, organization_id)
    return bool(membership and membership.is_owner)


def _is_member(agent, organization_id):
    return _get_membership(agent, organization_id) is not None


# ---------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------

@login_required
def my_organizations(request):
    """
    Powers the Dashboard 'Organization' section.
    - Non-Owner / Owner limit: An agent associated with any organization cannot create another.
    """
    memberships = AgentOrganizationMapping.objects.filter(
        agent=request.user, status=AgentOrganizationMapping.Status.ACTIVE
    ).select_related("organization")

    user_associated_with_org = memberships.exists()

    organizations = [
        {
            "org": m.organization,
            "is_owner": m.is_owner,
            "role": "Owner" if m.is_owner else "Member",
        }
        for m in memberships
    ]

    return render(
        request,
        "agent/organization_list.html",
        {
            "organizations": organizations,
            "has_organizations": bool(organizations),
            "can_create_org": not user_associated_with_org,
        },
    )


@login_required
def create_organization(request):
    """
    Organization Creation Flow:
    - Strictly limits each agent associated with an org from creating another.
    """
    # Check if agent is already associated with any active organization (as owner or member)
    already_associated = AgentOrganizationMapping.objects.filter(
        agent=request.user,
        status=AgentOrganizationMapping.Status.ACTIVE,
    ).exists()

    if already_associated:
        messages.error(
            request,
            "You are already associated with an organization. You cannot create another organization."
        )
        return redirect("organization:my-organizations")

    errors = {}
    data = {}

    if request.method == "POST":
        data = {
            "organization_name": request.POST.get("organization_name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "city": request.POST.get("city", "").strip(),
            "state": request.POST.get("state", "").strip(),
            "country": request.POST.get("country", "").strip(),
            "zip_code": request.POST.get("zip_code", "").strip(),
            "website": request.POST.get("website", "").strip(),
        }
        logo = request.FILES.get("logo")

        # ---- Step 1: Validate ----
        if not data["organization_name"]:
            errors["organization_name"] = "Organization name is required."

        if data["phone"] and not data["phone"].replace("+", "").isdigit():
            errors["phone"] = "Phone number must contain only digits."

        if not errors:
            with transaction.atomic():
                # ---- Step 2: Insert into Organization Master table ----
                organization = Organization.objects.create(
                    organization_name=data["organization_name"],
                    email=data["email"] or None,
                    phone=data["phone"] or None,
                    address=data["address"] or None,
                    city=data["city"] or None,
                    state=data["state"] or None,
                    country=data["country"] or None,
                    zip_code=data["zip_code"] or None,
                    website=data["website"] or None,
                    logo=logo,
                    created_by=request.user,
                )

                # ---- Step 3: Mapping row, creator becomes Owner ----
                AgentOrganizationMapping.objects.create(
                    agent=request.user,
                    organization=organization,
                    is_owner=True,
                    status=AgentOrganizationMapping.Status.ACTIVE,
                )

            messages.success(
                request,
                f'Organization "{organization.organization_name}" created successfully. '
                f"You are now the Owner.",
            )
            return redirect("organization:detail", organization_id=organization.id)

    return render(
        request, "agent/organization_create.html", {"errors": errors, "data": data}
    )


@login_required
def edit_organization(request, organization_id):
    """OWNER ONLY - Edit/Update organization details."""
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can edit organization information.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    errors = {}

    if request.method == "POST":
        org_name = request.POST.get("organization_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        country = request.POST.get("country", "").strip()
        zip_code = request.POST.get("zip_code", "").strip()
        website = request.POST.get("website", "").strip()
        logo = request.FILES.get("logo")

        if not org_name:
            errors["organization_name"] = "Organization name is required."

        if phone and not phone.replace("+", "").isdigit():
            errors["phone"] = "Phone number must contain only digits."

        if not errors:
            organization.organization_name = org_name
            organization.email = email or None
            organization.phone = phone or None
            organization.address = address or None
            organization.city = city or None
            organization.state = state or None
            organization.country = country or None
            organization.zip_code = zip_code or None
            organization.website = website or None
            if logo:
                organization.logo = logo
            organization.save()

            messages.success(request, f'Organization "{organization.organization_name}" updated successfully.')
            return redirect("organization:detail", organization_id=organization.id)

    return render(
        request, "agent/organization_edit.html", {"organization": organization, "errors": errors}
    )


@login_required
def organization_detail(request, organization_id):
    """View organization details - visible to BOTH Owner and Member."""
    if not _is_member(request.user, organization_id):
        messages.error(request, "You are not a member of this organization.")
        raise PermissionDenied("You are not linked to this organization.")

    organization = get_object_or_404(Organization, id=organization_id)
    owner_flag = _is_owner(request.user, organization_id)

    return render(
        request,
        "agent/organization_detail.html",
        {"organization": organization, "is_owner": owner_flag},
    )


@login_required
def organization_members(request, organization_id):
    """Manage organization members list - Owner + Member can view."""
    if not _is_member(request.user, organization_id):
        messages.error(request, "You are not a member of this organization.")
        raise PermissionDenied("You are not linked to this organization.")

    organization = get_object_or_404(Organization, id=organization_id)
    owner_flag = _is_owner(request.user, organization_id)

    members = AgentOrganizationMapping.objects.filter(
        organization=organization, status=AgentOrganizationMapping.Status.ACTIVE
    ).select_related("agent")

    return render(
        request,
        "agent/manage_members.html",
        {"organization": organization, "members": members, "is_owner": owner_flag},
    )


@login_required
def add_agent(request, organization_id):
    """
    OWNER ONLY - 'Add new agents' action.
    Step 1: Enter agent details & validate.
    Step 2: Create the agent record (if the agent does not already exist).
    Step 3: Create record in AgentOrganizationMapping table (is_owner=False).
    """
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can do that.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    error = None

    if request.method == "POST":
        identifier = request.POST.get("agent_identifier", "").strip()

        if not identifier:
            error = "Please enter username or email."
        else:
            # Step 2: Find or create the agent record if it doesn't exist
            new_agent = User.objects.filter(username=identifier).first() or \
                User.objects.filter(email=identifier).first()

            if not new_agent:
                # Create the agent record if it does not already exist
                is_email = "@" in identifier
                username = identifier if not is_email else identifier.split("@")[0]
                email = identifier if is_email else f"{identifier}@example.com"
                
                # Make username unique if already taken
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                from django.contrib.auth.models import Group

                new_agent = User.objects.create_user(
                    username=username,
                    email=email,
                    password="Password123!" # Default temporary password
                )
                agent_group, _ = Group.objects.get_or_create(name='agent')
                new_agent.groups.add(agent_group)

                messages.info(request, f"New agent account '{username}' created automatically with default password 'Password123!'.")

            # Step 3: Create mapping record with is_owner = False
            mapping, created = AgentOrganizationMapping.objects.get_or_create(
                agent=new_agent,
                organization=organization,
                defaults={
                    "is_owner": False,  # newly added agents are always regular Members
                    "status": AgentOrganizationMapping.Status.ACTIVE,
                },
            )

            # If mapping previously existed but status was REMOVED, reactivate it
            if not created and mapping.status != AgentOrganizationMapping.Status.ACTIVE:
                mapping.status = AgentOrganizationMapping.Status.ACTIVE
                mapping.save(update_fields=["status", "updated_at"])
                created = True

            if created:
                messages.success(
                    request, f"{new_agent.username} added to {organization.organization_name} as a Member."
                )
                return redirect("organization:members", organization_id=organization.id)
            else:
                error = f"Agent '{new_agent.username}' is already a member of this organization."

    return render(
        request, "agent/add_agent.html", {"organization": organization, "error": error}
    )


@login_required
def remove_agent(request, organization_id, mapping_id):
    """OWNER ONLY - part of 'Manage organization members'."""
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can do that.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    mapping = get_object_or_404(
        AgentOrganizationMapping, id=mapping_id, organization=organization
    )

    if mapping.is_owner:
        messages.error(request, "You cannot remove the organization owner.")
    elif request.method == "POST":
        mapping.status = AgentOrganizationMapping.Status.REMOVED
        mapping.save(update_fields=["status", "updated_at"])
        messages.success(request, f"{mapping.agent.username} removed from organization.")

    return redirect("organization:members", organization_id=organization.id)