from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    InvestorProfile, InvestmentListing, Investment, ROIData,
    InvestorDocument, InvestorMeeting
)
from Apps.PublicPage.models import Property


class InvestorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = InvestorProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'investor_type',
                 'company_name', 'contact_person', 'phone', 'risk_tolerance',
                 'investment_range_min', 'investment_range_max', 'preferred_property_types',
                 'verified', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'verified']


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'title', 'price', 'location', 'property_type', 'description']


class InvestmentListingSerializer(serializers.ModelSerializer):
    property_details = PropertySerializer(source='property_obj', read_only=True)
    total_invested = serializers.ReadOnlyField(source='total_invested_amount')
    investment_percentage_filled = serializers.ReadOnlyField()

    class Meta:
        model = InvestmentListing
        fields = ['id', 'property_obj', 'property_details', 'title', 'description',
                 'investment_type', 'total_investment_needed', 'minimum_investment',
                 'expected_roi_percentage', 'investment_term_months', 'status',
                 'featured', 'created_at', 'updated_at', 'closes_at',
                 'total_invested', 'investment_percentage_filled']
        read_only_fields = ['created_at', 'updated_at']


class InvestmentSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source='investor.username', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    property_title = serializers.CharField(source='listing.property_obj.title', read_only=True)

    class Meta:
        model = Investment
        fields = ['id', 'investor', 'investor_name', 'listing', 'listing_title',
                 'property_title', 'amount', 'status', 'investment_date',
                 'confirmed_date', 'notes']
        read_only_fields = ['investment_date', 'confirmed_date', 'investor']


class ROIDataSerializer(serializers.ModelSerializer):
    investment_details = InvestmentSerializer(source='investment', read_only=True)

    class Meta:
        model = ROIData
        fields = ['id', 'investment', 'investment_details', 'actual_roi_percentage',
                 'total_returns', 'last_payment_date', 'next_payment_date',
                 'payment_frequency', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class InvestorDocumentSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source='investor.username', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)

    class Meta:
        model = InvestorDocument
        fields = ['id', 'investor', 'investor_name', 'document_type', 'title',
                 'file', 'uploaded_at', 'verified', 'verified_by', 'verified_by_name',
                 'verified_at']
        read_only_fields = ['uploaded_at', 'verified', 'verified_by', 'verified_at']


class InvestorMeetingSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source='investor.username', read_only=True)

    class Meta:
        model = InvestorMeeting
        fields = ['id', 'investor', 'investor_name', 'meeting_type', 'title',
                 'description', 'scheduled_date', 'duration_minutes', 'location',
                 'meeting_link', 'status', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# Create serializers
class CreateInvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = ['listing', 'amount', 'notes']


class CreateInvestorDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorDocument
        fields = ['document_type', 'title', 'file']


class CreateInvestorMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorMeeting
        fields = ['meeting_type', 'title', 'description', 'scheduled_date',
                 'duration_minutes', 'location', 'meeting_link', 'notes']


class UpdateInvestmentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = ['status']


class UpdateROIDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ROIData
        fields = ['actual_roi_percentage', 'total_returns', 'last_payment_date',
                 'next_payment_date', 'payment_frequency']
