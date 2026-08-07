from django.contrib import admin
from .models import Organization, AgentOrganizationMapping


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