from django.db import models
import uuid
from django.conf import settings
from django.core.validators import RegexValidator
from django.urls import reverse


class Organization(models.Model):
    """
    Master table -> stores organization / company information.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    id = models.BigAutoField(primary_key=True)

    organization_name = models.CharField(max_length=255)

    organization_code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        blank=True,  # auto-generated in save() if left blank
    )

    email = models.EmailField(blank=True, null=True)

    phone_validator = RegexValidator(
        regex=r"^\+?[0-9]{7,15}$",
        message="Phone number must be 7 to 15 digits, optionally starting with +.",
    )
    phone = models.CharField(
        max_length=20, blank=True, null=True, validators=[phone_validator]
    )

    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    logo = models.ImageField(upload_to="organization_logos/", blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return f"{self.organization_name} ({self.organization_code})"

    def save(self, *args, **kwargs):
        if not self.organization_code:
            self.organization_code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def _generate_unique_code(self):
        base = "".join(
            ch for ch in self.organization_name.upper() if ch.isalnum()
        )[:3] or "ORG"
        while True:
            candidate = f"{base}-{uuid.uuid4().hex[:6].upper()}"
            if not Organization.objects.filter(organization_code=candidate).exists():
                return candidate

    def get_absolute_url(self):
        return reverse("organization:detail", args=[self.id])


class AgentOrganizationMapping(models.Model):
    """
    Relationship table -> links Agents (users) to Organizations.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        REMOVED = "removed", "Removed"

    id = models.BigAutoField(primary_key=True)

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="member_mappings",
    )

    is_owner = models.BooleanField(default=False)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-joined_at"]
        verbose_name = "Agent Organization Mapping"
        verbose_name_plural = "Agent Organization Mappings"
        constraints = [
            models.UniqueConstraint(
                fields=["agent", "organization"],
                name="unique_agent_per_organization",
            )
        ]

    def __str__(self):
        role = "Owner" if self.is_owner else "Member"
        return f"{self.agent} -> {self.organization} ({role})"