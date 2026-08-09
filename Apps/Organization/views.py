from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from Apps.Administration.backends import AUTH_BACKEND_PATH
from Apps.Administration.models import ActivityLog

from .forms import InviteAgentForm, CreateAccountFromInvitationForm
from .invitation_utils import (
    build_invitation_absolute_url,
    complete_agent_invitation,
    create_agent_invitation,
    resend_agent_invitation,
    send_invitation_email,
)
from .models import Organization, AgentOrganizationMapping, AgentInvitation

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


def _log_org_event(user, action_type, description, request=None):
    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        module="organization",
        description=description,
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )


def _safe_invitation(mapping):
    try:
        return mapping.invitation
    except AgentInvitation.DoesNotExist:
        return None


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

    user_associated_with_org = AgentOrganizationMapping.objects.filter(
        agent=request.user,
        status__in=[
            AgentOrganizationMapping.Status.ACTIVE,
            AgentOrganizationMapping.Status.PENDING_INVITATION,
        ],
    ).exists()

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
    already_associated = AgentOrganizationMapping.objects.filter(
        agent=request.user,
        status__in=[
            AgentOrganizationMapping.Status.ACTIVE,
            AgentOrganizationMapping.Status.PENDING_INVITATION,
        ],
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

        if not data["organization_name"]:
            errors["organization_name"] = "Organization name is required."

        if data["phone"] and not data["phone"].replace("+", "").isdigit():
            errors["phone"] = "Phone number must contain only digits."

        if not errors:
            with transaction.atomic():
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
    """Manage organization members / agent invitations - Owner + Member can view."""
    if not _is_member(request.user, organization_id):
        messages.error(request, "You are not a member of this organization.")
        raise PermissionDenied("You are not linked to this organization.")

    organization = get_object_or_404(Organization, id=organization_id)
    owner_flag = _is_owner(request.user, organization_id)

    members = (
        AgentOrganizationMapping.objects.filter(organization=organization)
        .exclude(status=AgentOrganizationMapping.Status.REMOVED)
        .select_related("agent", "invitation")
        .order_by("-is_owner", "-created_at")
    )

    member_rows = []
    for m in members:
        invitation = _safe_invitation(m)
        invite_url = None
        if (
            invitation
            and invitation.status == AgentInvitation.Status.PENDING
            and owner_flag
        ):
            invite_url = build_invitation_absolute_url(request, invitation)

        member_rows.append(
            {
                "mapping": m,
                "invitation": invitation,
                "invite_url": invite_url,
                "status_label": m.invitation_status_label,
            }
        )

    return render(
        request,
        "agent/manage_members.html",
        {
            "organization": organization,
            "member_rows": member_rows,
            "is_owner": owner_flag,
        },
    )


@login_required
def add_agent(request, organization_id):
    """
    OWNER ONLY - Invite a new agent by email.
    Creates a pending user with a hashed temporary password and an invitation token.
    """
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can do that.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    form = InviteAgentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            invitation = create_agent_invitation(
                organization=organization,
                invited_by=request.user,
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                phone=form.cleaned_data["phone"],
                request=request,
            )
            email_ok, email_msg = send_invitation_email(request, invitation)
            invite_url = build_invitation_absolute_url(request, invitation)

            if email_ok:
                messages.success(
                    request,
                    f"Invitation sent to {invitation.email}. "
                    f"You can also copy the link from the members list.",
                )
            else:
                messages.warning(
                    request,
                    f"{email_msg} Copy the invitation link from the members list: {invite_url}",
                )
            return redirect("organization:members", organization_id=organization.id)
        except ValueError as exc:
            form.add_error(None, str(exc))

    return render(
        request,
        "agent/add_agent.html",
        {"organization": organization, "form": form},
    )


@login_required
@require_POST
def resend_invitation(request, organization_id, mapping_id):
    """OWNER ONLY - Resend a pending invitation email."""
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can do that.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    mapping = get_object_or_404(
        AgentOrganizationMapping, id=mapping_id, organization=organization
    )
    invitation = _safe_invitation(mapping)
    if not invitation or invitation.status != AgentInvitation.Status.PENDING:
        messages.error(request, "No pending invitation found for this agent.")
        return redirect("organization:members", organization_id=organization.id)

    try:
        success, message = resend_agent_invitation(
            request, invitation, resent_by=request.user
        )
        if success:
            messages.success(request, f"Invitation resent to {invitation.email}.")
        else:
            messages.warning(request, message)
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("organization:members", organization_id=organization.id)


@login_required
@require_POST
def deactivate_agent(request, organization_id, mapping_id):
    """OWNER ONLY - Deactivate an agent (keeps record, blocks org access)."""
    if not _is_owner(request.user, organization_id):
        messages.error(request, "Only the organization owner can do that.")
        raise PermissionDenied("You must be the organization owner.")

    organization = get_object_or_404(Organization, id=organization_id)
    mapping = get_object_or_404(
        AgentOrganizationMapping, id=mapping_id, organization=organization
    )

    if mapping.is_owner:
        messages.error(request, "You cannot deactivate the organization owner.")
        return redirect("organization:members", organization_id=organization.id)

    mapping.status = AgentOrganizationMapping.Status.INACTIVE
    mapping.save(update_fields=["status", "updated_at"])

    invitation = _safe_invitation(mapping)
    if invitation and invitation.status == AgentInvitation.Status.PENDING:
        invitation.status = AgentInvitation.Status.REVOKED
        invitation.save(update_fields=["status", "updated_at"])

    _log_org_event(
        request.user,
        "update",
        f"Deactivated agent {mapping.agent.email} in {organization.organization_name}.",
        request=request,
    )
    messages.success(
        request, f"{mapping.agent.get_full_name() or mapping.agent.email} has been deactivated."
    )
    return redirect("organization:members", organization_id=organization.id)


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

        invitation = _safe_invitation(mapping)
        if invitation and invitation.status == AgentInvitation.Status.PENDING:
            invitation.status = AgentInvitation.Status.REVOKED
            invitation.save(update_fields=["status", "updated_at"])

        messages.success(request, f"{mapping.agent.username} removed from organization.")

    return redirect("organization:members", organization_id=organization.id)


def create_account(request, token):
    """
    Public create-account page for invitation token.
    Valid pending tokens allow the agent to set a password and activate.
    Used/revoked tokens show an appropriate message.
    """
    invitation = AgentInvitation.objects.filter(token=token).select_related(
        "agent", "organization", "mapping"
    ).first()

    if not invitation:
        return render(
            request,
            "auth/create_account.html",
            {
                "invalid": True,
                "message": "This invitation link is invalid.",
            },
        )

    if invitation.status == AgentInvitation.Status.USED:
        return render(
            request,
            "auth/create_account.html",
            {
                "already_used": True,
                "message": "This invitation has already been used. Please log in with your account.",
            },
        )

    if invitation.status == AgentInvitation.Status.REVOKED:
        return render(
            request,
            "auth/create_account.html",
            {
                "invalid": True,
                "message": "This invitation has been revoked. Please contact your organization owner.",
            },
        )

    agent = invitation.agent
    initial = {
        "first_name": agent.first_name,
        "last_name": agent.last_name,
        "phone": getattr(getattr(agent, "agent_profile", None), "phone", "") or "",
    }
    form = CreateAccountFromInvitationForm(
        request.POST or None, user=agent, initial=initial
    )

    if request.method == "POST" and form.is_valid():
        try:
            user = complete_agent_invitation(
                invitation,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                phone=form.cleaned_data["phone"],
                password=form.cleaned_data["password1"],
                request=request,
            )
            login(request, user, backend=AUTH_BACKEND_PATH)
            from Apps.Subscriptions.utils import auto_assign_free_plan

            auto_assign_free_plan(user)
            messages.success(
                request,
                "Your account has been created successfully. Welcome!",
            )
            return redirect("agent:dashboard")
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("create-account", token=token)

    return render(
        request,
        "auth/create_account.html",
        {
            "form": form,
            "invitation": invitation,
            "organization": invitation.organization,
            "email": invitation.email,
        },
    )
