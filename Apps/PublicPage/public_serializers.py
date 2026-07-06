from rest_framework import serializers
from .models import Property, PropertyImage


class PublicPropertySerializer(serializers.ModelSerializer):
    """Serializer for public-facing property data with limited information"""
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'price', 'location', 'property_type', 
            'category', 'public_description', 'bedrooms', 'bathrooms', 
            'area_sqft', 'is_featured', 'image'
        ]
    
    def get_image(self, obj):
        """Get the primary image for the property"""
        primary_image = obj.images.filter(category='General').first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        return None


class AuthenticatedPropertySerializer(serializers.ModelSerializer):
    """Serializer for authenticated users with role-based data access"""
    images = serializers.SerializerMethodField()
    can_view_details = serializers.SerializerMethodField()
    investment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'price', 'location', 'property_type', 
            'category', 'description', 'bedrooms', 'bathrooms', 'area_sqft',
            'is_featured', 'investment_opportunity', 'images', 'can_view_details',
            'investment_details', 'created_at', 'updated_at'
        ]
    
    def get_images(self, obj):
        """Get all images for the property"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            images = obj.images.all()
            return [
                {
                    'id': img.id,
                    'url': img.image.url if img.image else None,
                    'category': img.category
                }
                for img in images
            ]
        return []
    
    def get_can_view_details(self, obj):
        """Check if user can view full details"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_access_by_role(request.user)
        return False
    
    def get_investment_details(self, obj):
        """Get investment details for investors"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from Apps.Administration.auth_utils import get_user_role
            user_role = get_user_role(request.user)
            
            if user_role == 'investor' and obj.investment_opportunity:
                return {
                    'expected_roi': obj.expected_roi,
                    'minimum_investment': obj.minimum_investment,
                }
        return None


class PropertyImageSerializer(serializers.ModelSerializer):
    """Serializer for property images"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'category']
    
    def get_image_url(self, obj):
        """Get full image URL"""
        if obj.image:
            return obj.image.url
        return None


class PublicPropertyListSerializer(serializers.ModelSerializer):
    """Minimal serializer for property listings"""
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = ['id', 'title', 'slug', 'price', 'location', 'property_type', 'image']
    
    def get_image(self, obj):
        """Get the primary image for the property"""
        primary_image = obj.images.filter(category='General').first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        return None
