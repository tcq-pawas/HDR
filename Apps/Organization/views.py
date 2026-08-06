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
    - Limit: An agent can only create/own 1 organization.
    """
    memberships = AgentOrganizationMapping.objects.filter(
        agent=request.user, status=AgentOrganizationMapping.Status.ACTIVE
    ).select_related("organization")

    user_owns_org = any(m.is_owner for m in memberships)

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
            "can_create_org": not user_owns_org,
        },
    )


@login_required
def create_organization(request):
    """
    Organization Creation Flow:
    - Strictly limits each agent to owning maximum 1 organization.
    """
    # Check if agent already owns an organization
    already_owns_org = AgentOrganizationMapping.objects.filter(
        agent=request.user,
        is_owner=True,
        status=AgentOrganizationMapping.Status.ACTIVE,
    ).exists()

    if already_owns_org:
        messages.error(
            request,
            "You are already the owner of an organization. Each agent can only create 1 organization."
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
    """OWNER ONLY - 'Add new agents' action."""
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can do that.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    error = None

    if request.method == "POST":
        identifier = request.POST.get("agent_identifier", "").strip()
        new_agent = User.objects.filter(username=identifier).first() or \
            User.objects.filter(email=identifier).first()

        if not new_agent:
            error = "No agent found with that username/email."
        else:
            mapping, created = AgentOrganizationMapping.objects.get_or_create(
                agent=new_agent,
                organization=organization,
                defaults={
                    "is_owner": False,  # added agents are always Members
                    "status": AgentOrganizationMapping.Status.ACTIVE,
                },
            )
            if created:
                messages.success(
                    request, f"{new_agent.username} added to {organization.organization_name}."
                )
                return redirect("organization:members", organization_id=organization.id)
            else:
                error = "This agent is already part of the organization."

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