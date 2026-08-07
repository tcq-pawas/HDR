from django.urls import path
from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.my_organizations, name="my-organizations"),
    path("create/", views.create_organization, name="create"),
    path("organizations/", views.organization_list, name="organization_list"),
    path("<int:organization_id>/", views.organization_detail, name="detail"),
    path("<int:organization_id>/edit/", views.edit_organization, name="edit"),
    path("<int:organization_id>/members/", views.organization_members, name="members"),
    path("<int:organization_id>/members/add/", views.add_agent, name="add-agent"),
    path(
        "<int:organization_id>/members/<int:mapping_id>/remove/",
        views.remove_agent,
        name="remove-agent",
    ),
]