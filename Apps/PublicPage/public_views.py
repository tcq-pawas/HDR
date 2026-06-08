from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from Apps.Administration.auth_utils import get_user_role, role_required
from .models import Property, PropertyImage
from .public_serializers import (
    PublicPropertySerializer, AuthenticatedPropertySerializer,
    PropertyImageSerializer, PublicPropertyListSerializer
)


class PublicPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for public property access with role-based data filtering"""
    queryset = Property.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['property_type', 'category', 'bedrooms', 'bathrooms']
    search_fields = ['title', 'location', 'public_description']
    ordering_fields = ['price', 'created_at', 'area_sqft']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on authentication status"""
        request = self.get_serializer_context()['request']
        
        if request.user.is_authenticated:
            return AuthenticatedPropertySerializer
        else:
            return PublicPropertySerializer
    
    def get_queryset(self):
        """Filter queryset based on user authentication and role"""
        request = self.request
        queryset = Property.objects.filter(is_active=True)
        
        if not request.user.is_authenticated:
            # Public users can only see properties marked for public viewing
            queryset = queryset.filter(show_to_public=True)
        else:
            # Authenticated users can see properties they have access to
            user_role = get_user_role(request.user)
            if user_role:
                # Filter by allowed roles
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(allowed_roles='all') | 
                    Q(allowed_roles=user_role)
                )
            else:
                # Authenticated user without specific role
                queryset = queryset.filter(allowed_roles='all')
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve property details with role-based access control"""
        instance = self.get_object()
        
        # Check if user has access to this property
        if not request.user.is_authenticated and not instance.can_view_public():
            return Response(
                {'error': 'This property requires authentication to view.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.is_authenticated and not instance.can_access_by_role(request.user):
            return Response(
                {'error': 'You do not have permission to view this property.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured properties"""
        queryset = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def investment_opportunities(self, request):
        """Get investment opportunities (investors only)"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required to view investment opportunities.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_role = get_user_role(request.user)
        if user_role != 'investor':
            return Response(
                {'error': 'This endpoint is only available to investors.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(investment_opportunity=True)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PropertyImageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for property images with access control"""
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter images based on property access"""
        property_id = self.kwargs.get('property_pk')
        if property_id:
            property_obj = get_object_or_404(Property, id=property_id)
            
            # Check if user has access to the property
            if not self.request.user.is_authenticated and not property_obj.can_view_public():
                return PropertyImage.objects.none()
            
            if self.request.user.is_authenticated and not property_obj.can_access_by_role(self.request.user):
                return PropertyImage.objects.none()
            
            return PropertyImage.objects.filter(property=property_obj)
        
        return PropertyImage.objects.none()


def public_property_list(request):
    """Template view for public property listing page"""
    properties = Property.objects.filter(
        is_active=True, 
        show_to_public=True
    ).order_by('-created_at')
    
    context = {
        'properties': properties,
        'is_authenticated': request.user.is_authenticated,
        'user_role': get_user_role(request.user) if request.user.is_authenticated else None,
    }
    
    return render(request, 'public/property_list.html', context)


def public_property_detail(request, slug):
    """Template view for public property detail page"""
    property_obj = get_object_or_404(Property, slug=slug, is_active=True)
    
    # Check access permissions
    if not request.user.is_authenticated and not property_obj.can_view_public():
        return render(request, 'auth/unauthorized.html', status=403)
    
    if request.user.is_authenticated and not property_obj.can_access_by_role(request.user):
        return render(request, 'auth/unauthorized.html', status=403)
    
    # Get appropriate data based on user status
    if request.user.is_authenticated:
        property_data = property_obj.get_authenticated_data(request.user)
        images = property_obj.images.all()
    else:
        property_data = property_obj.get_public_data()
        images = property_obj.images.filter(category='General')  # Only show general images to public
    
    context = {
        'property': property_obj,
        'property_data': property_data,
        'images': images,
        'is_authenticated': request.user.is_authenticated,
        'user_role': get_user_role(request.user) if request.user.is_authenticated else None,
    }
    
    return render(request, 'public/property_detail.html', context)


def public_home(request):
    """Template view for public home page"""
    featured_properties = Property.objects.filter(
        is_active=True, 
        show_to_public=True, 
        is_featured=True
    ).order_by('-created_at')[:6]
    
    recent_properties = Property.objects.filter(
        is_active=True, 
        show_to_public=True
    ).order_by('-created_at')[:8]
    
    context = {
        'featured_properties': featured_properties,
        'recent_properties': recent_properties,
        'is_authenticated': request.user.is_authenticated,
        'user_role': get_user_role(request.user) if request.user.is_authenticated else None,
    }
    
    return render(request, 'public/home.html', context)
