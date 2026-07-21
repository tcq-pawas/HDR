"""
Serializers for Contact Inquiry API
Handles dynamic validation based on website configuration
"""

import logging
from rest_framework import serializers
from .constants import WEBSITE_CONFIG, CONTACT_METHOD_CHOICES, PROPERTY_TYPE_CHOICES, BUDGET_RANGE_CHOICES, AREA_SIZE_CHOICES
from .validators import WebsiteValidator, PhoneNumberValidator, EmailValidatorCustom, validate_required_fields_for_website


logger = logging.getLogger('contact_inquiry_api')


class ContactInquirySerializer(serializers.Serializer):
    """
    Dynamic serializer for contact inquiries
    Validates fields based on website configuration
    """
    
    # Required for all websites
    website = serializers.CharField(max_length=50, validators=[WebsiteValidator()])
    full_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20, validators=[PhoneNumberValidator()])
    email = serializers.EmailField(validators=[EmailValidatorCustom()])
    
    # Optional fields (required based on website)
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True)
    preferred_contact_method = serializers.ChoiceField(
        choices=CONTACT_METHOD_CHOICES,
        required=False,
        allow_blank=True
    )
    property_type = serializers.ChoiceField(
        choices=PROPERTY_TYPE_CHOICES,
        required=False,
        allow_blank=True
    )
    preferred_location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    budget_range = serializers.ChoiceField(
        choices=BUDGET_RANGE_CHOICES,
        required=False,
        allow_blank=True
    )
    area_size = serializers.ChoiceField(
        choices=AREA_SIZE_CHOICES,
        required=False,
        allow_blank=True
    )
    message = serializers.CharField(required=False, allow_blank=True)
    
    # Metadata fields (auto-populated from request)
    source_url = serializers.URLField(required=False, allow_blank=True)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """
        Dynamic validation based on website configuration
        """
        website = attrs.get('website')
        
        if not website:
            raise serializers.ValidationError({"website": ["This field is required."]})
        
        # Validate required fields for the specific website
        errors = validate_required_fields_for_website(website, attrs)
        
        if errors:
            raise serializers.ValidationError(errors)
        
        # Sanitize text inputs to prevent XSS
        from .utils import sanitize_input
        
        for field in ['full_name', 'subject', 'preferred_location', 'message']:
            if field in attrs and attrs[field]:
                attrs[field] = sanitize_input(attrs[field])
        
        return attrs
    
    def create(self, validated_data):
        """
        Create and return a new ContactInquiry instance
        """
        from .models import WebsiteInquiry
        
        try:
            # Extract metadata fields (they may not be in validated_data)
            request = self.context.get('request')
            if request:
                from .utils import get_client_ip, get_user_agent, get_source_url
                
                validated_data['ip_address'] = get_client_ip(request)
                validated_data['user_agent'] = get_user_agent(request)
                validated_data['source_url'] = get_source_url(request)
            
            # Create the inquiry
            inquiry = WebsiteInquiry.objects.create(**validated_data)
            
            logger.info(
                f"Contact inquiry created successfully for website {inquiry.website} "
                f"from {inquiry.email}"
            )
            
            return inquiry
            
        except Exception as e:
            logger.error(
                f"Failed to create contact inquiry: {str(e)}",
                exc_info=True
            )
            raise serializers.ValidationError(
                "Failed to save inquiry. Please try again later."
            )


class ContactInquiryResponseSerializer(serializers.Serializer):
    """
    Standard response serializer for contact inquiry API
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    errors = serializers.DictField(required=False, allow_null=True)
