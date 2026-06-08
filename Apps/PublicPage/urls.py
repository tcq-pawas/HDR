from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .public_views import (
    PublicPropertyViewSet, PropertyImageViewSet,
    public_property_list, public_property_detail, public_home
)

app_name = 'public'

router = DefaultRouter()
router.register(r'properties', PublicPropertyViewSet, basename='property-api')
router.register(r'images', PropertyImageViewSet, basename='property-image-api')

urlpatterns = [
    # Public pages (view-only with limited data)
    path('', public_home, name='home'),
    path('properties/', public_property_list, name='property_list'),
    path('p/<slug:slug>/', public_property_detail, name='property_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('gallery/', views.media_page, name='media'),
    
    # API endpoints
    path('api/', include(router.urls)),
]