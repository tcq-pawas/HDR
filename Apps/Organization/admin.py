from django.contrib import admin
from .models import Organization, AgentOrganizationMapping, AgentInvitation


class AgentOrganizationMappingInline(admin.TabularInline):
    model = AgentOrganizationMapping
    extra = 0
    autocomplete_fields = ["agent"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization_name",
        "organization_code",
        "status",
        "created_by",
        "created_at",
    )
    search_fields = ("organization_name", "organization_code", "email")
    list_filter = ("status",)
    inlines = [AgentOrganizationMappingInline]


@admin.register(AgentOrganizationMapping)
class AgentOrganizationMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "organization", "is_owner", "status", "joined_at")
    list_filter = ("is_owner", "status")
    search_fields = ("agent__username", "organization__organization_name")
    autocomplete_fields = ["agent", "organization"]


@admin.register(AgentInvitation)
class AgentInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "organization",
        "status",
        "invited_by",
        "created_at",
        "used_at",
        "last_sent_at",
    )
    list_filter = ("status",)
    search_fields = ("email", "token", "organization__organization_name")
    autocomplete_fields = ["agent", "organization", "mapping", "invited_by"]
    readonly_fields = ("token", "created_at", "updated_at", "used_at")