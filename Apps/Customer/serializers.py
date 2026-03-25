from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CustomerProfile, Inquiry, SavedProperty, PropertyViewing, CustomerFeedback
from Apps.PublicPage.models import Property


class CustomerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = CustomerProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                 'profile_picture', 'preferred_contact_method', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class InquirySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = Inquiry
        fields = ['id', 'customer', 'customer_name', 'property', 'property_title', 
                 'subject', 'message', 'status', 'priority', 'created_at', 
                 'updated_at', 'resolved_at']
        read_only_fields = ['created_at', 'updated_at', 'resolved_at', 'customer']


class SavedPropertySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    property_details = serializers.SerializerMethodField()

    class Meta:
        model = SavedProperty
        fields = ['id', 'customer', 'customer_name', 'property', 'property_details', 
                 'saved_at', 'notes']
        read_only_fields = ['saved_at', 'customer']

    def get_property_details(self, obj):
        if obj.property:
            return {
                'id': obj.property.id,
                'title': obj.property.title,
                'price': obj.property.price,
                'location': obj.property.location,
                'property_type': obj.property.property_type,
            }
        return None


class PropertyViewingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = PropertyViewing
        fields = ['id', 'customer', 'customer_name', 'property', 'property_title', 
                 'scheduled_date', 'status', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'customer']


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = CustomerFeedback
        fields = ['id', 'customer', 'customer_name', 'property', 'property_title', 
                 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at', 'customer']


class CreateInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ['property', 'subject', 'message', 'priority']


class CreateSavedPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedProperty
        fields = ['property', 'notes']


class CreatePropertyViewingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyViewing
        fields = ['property', 'scheduled_date', 'notes']


class CreateCustomerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = ['property', 'rating', 'comment']
