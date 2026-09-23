import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from Apps.Administration.auth_utils import assign_user_group
from Apps.Administration.models import ActivityLog
from Apps.Agent.models import AgentProfile

from .models import AgentInvitation, AgentOrganizationMapping

User = get_user_model()
logger = logging.getLogger(__name__)


def _log_invitation_event(user, action_type, description, request=None):
    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        module="agent_invitation",
        description=description,
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )


def _unique_username_from_email(email):
    base = email.split("@")[0][:120] or "agent"
    # Prefer alphanumeric usernames
    base = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in base)
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username


def generate_temporary_password(length=20):
    return secrets.token_urlsafe(length)[:length]


def build_invitation_absolute_url(request, invitation):
    path = reverse("create-account", kwargs={"token": invitation.token})
    return request.build_absolute_uri(path)


def send_invitation_email(request, invitation):
    """Send (or resend) the agent invitation email. Returns (success, message)."""
    invite_url = build_invitation_absolute_url(request, invitation)
    organization = invitation.organization
    context = {
        "organization_name": organization.organization_name,
        "invite_url": invite_url,
        "agent_email": invitation.email,
        "invited_by": invitation.invited_by.get_full_name()
        if invitation.invited_by
        else "Organization Owner",
    }
    subject = f"You're invited to join {organization.organization_name} on HHectare"
    try:
        html_message = render_to_string(
            "organization/email/agent_invitation.html", context
        )
        plain_message = strip_tags(html_message)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            html_message=html_message,
            fail_silently=False,
        )
        invitation.last_sent_at = timezone.now()
        invitation.save(update_fields=["last_sent_at", "updated_at"])
        return True, "Invitation email sent."
    except Exception as exc:
        logger.exception("Failed to send agent invitation email: %s", exc)
        return False, f"Invitation created but email could not be sent: {exc}"


@transaction.atomic
def create_agent_invitation(
    *,
    organization,
    invited_by,
    email,
    first_name,
    last_name,
    phone,
    request=None,
):
    """
    Create a pending agent user + mapping + invitation token.
    Raises ValueError for validation / duplicate cases.
    """
    email = email.strip().lower()

    existing_pending = AgentInvitation.objects.filter(
        organization=organization,
        email__iexact=email,
        status=AgentInvitation.Status.PENDING,
    ).select_related("agent", "mapping").first()
    if existing_pending:
        raise ValueError(
            "A pending invitation already exists for this email. "
            "Use Resend Invitation from the members list."
        )

    existing_user = User.objects.filter(email__iexact=email).first()
    if existing_user and existing_user.is_active:
        # Active completed accounts cannot be re-invited
        pending = AgentInvitation.objects.filter(
            agent=existing_user, status=AgentInvitation.Status.PENDING
        ).exists()
        if not pending:
            raise ValueError(
                "This email is already associated with an active user account."
            )

    # One active/pending org membership per agent
    if existing_user:
        other_membership = (
            AgentOrganizationMapping.objects.filter(agent=existing_user)
            .exclude(status=AgentOrganizationMapping.Status.REMOVED)
            .exclude(organization=organization)
            .exists()
        )
        if other_membership:
            raise ValueError(
                "This agent is already associated with another organization."
            )

        existing_mapping = AgentOrganizationMapping.objects.filter(
            agent=existing_user, organization=organization
        ).first()
        if existing_mapping and existing_mapping.status in (
            AgentOrganizationMapping.Status.ACTIVE,
            AgentOrganizationMapping.Status.PENDING_INVITATION,
        ):
            raise ValueError(
                "This agent is already a member (or has a pending invitation) "
                "for this organization."
            )

    temp_password = generate_temporary_password()

    if existing_user and not existing_user.is_active:
        agent = existing_user
        agent.first_name = first_name
        agent.last_name = last_name
        agent.set_password(temp_password)
        agent.save(update_fields=["first_name", "last_name", "password"])
    else:
        agent = User.objects.create_user(
            username=_unique_username_from_email(email),
            email=email,
            password=temp_password,
            first_name=first_name,
            last_name=last_name,
            is_active=False,  # activated after invitation acceptance
        )

    assign_user_group(agent, "agent")

    profile, _ = AgentProfile.objects.get_or_create(user=agent)
    profile.phone = phone
    if not profile.company_name:
        profile.company_name = organization.organization_name
    profile.save()

    mapping = AgentOrganizationMapping.objects.filter(
        agent=agent, organization=organization
    ).first()
    if mapping:
        mapping.is_owner = False
        mapping.status = AgentOrganizationMapping.Status.PENDING_INVITATION
        mapping.save(update_fields=["is_owner", "status", "updated_at"])
    else:
        mapping = AgentOrganizationMapping.objects.create(
            agent=agent,
            organization=organization,
            is_owner=False,
            status=AgentOrganizationMapping.Status.PENDING_INVITATION,
        )

    # Revoke any prior non-pending invitations for this mapping
    AgentInvitation.objects.filter(mapping=mapping).exclude(
        status=AgentInvitation.Status.PENDING
    ).delete()

    invitation = AgentInvitation.objects.create(
        token=AgentInvitation.generate_token(),
        agent=agent,
        organization=organization,
        mapping=mapping,
        invited_by=invited_by,
        status=AgentInvitation.Status.PENDING,
        email=email,
    )

    _log_invitation_event(
        invited_by,
        "create",
        f"Created agent invitation for {email} to join "
        f"{organization.organization_name} (token={invitation.token[:8]}…).",
        request=request,
    )

    return invitation


def resend_agent_invitation(request, invitation, resent_by):
    if invitation.status != AgentInvitation.Status.PENDING:
        raise ValueError("This invitation is no longer pending and cannot be resent.")

    success, message = send_invitation_email(request, invitation)
    _log_invitation_event(
        resent_by,
        "update",
        f"Resent agent invitation to {invitation.email} for "
        f"{invitation.organization.organization_name}.",
        request=request,
    )
    return success, message


@transaction.atomic
def complete_agent_invitation(invitation, *, first_name, last_name, phone, password, request=None):
    if invitation.status != AgentInvitation.Status.PENDING:
        raise ValueError("This invitation has already been used.")

    agent = invitation.agent
    agent.first_name = first_name
    agent.last_name = last_name
    agent.set_password(password)
    agent.is_active = True
    agent.save()

    profile, _ = AgentProfile.objects.get_or_create(user=agent)
    profile.phone = phone
    profile.save(update_fields=["phone", "updated_at"])

    mapping = invitation.mapping
    mapping.status = AgentOrganizationMapping.Status.ACTIVE
    mapping.save(update_fields=["status", "updated_at"])

    invitation.mark_used()

    assign_user_group(agent, "agent")

    _log_invitation_event(
        agent,
        "update",
        f"Agent {agent.email} completed invitation onboarding for "
        f"{invitation.organization.organization_name}.",
        request=request,
    )

    return agent
