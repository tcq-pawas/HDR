from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import CustomerProfile, Inquiry, SavedProperty, PropertyViewing, CustomerFeedback
from .serializers import (
    CustomerProfileSerializer, InquirySerializer, SavedPropertySerializer,
    PropertyViewingSerializer, CustomerFeedbackSerializer,
    CreateInquirySerializer, CreateSavedPropertySerializer,
    CreatePropertyViewingSerializer, CreateCustomerFeedbackSerializer
)
from Apps.PublicPage.models import Property


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = CustomerProfile.objects.get_or_create(user=self.request.user)
        return profile


class InquiryListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inquiry.objects.filter(customer=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInquirySerializer
        return InquirySerializer

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class InquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InquirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inquiry.objects.filter(customer=self.request.user)


class SavedPropertyListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedProperty.objects.filter(customer=self.request.user).order_by('-saved_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateSavedPropertySerializer
        return SavedPropertySerializer

    def perform_create(self, serializer):
        property_obj = get_object_or_404(Property, id=serializer.validated_data['property'].id)
        serializer.save(customer=self.request.user, property=property_obj)


class SavedPropertyDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = SavedPropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedProperty.objects.filter(customer=self.request.user)


class PropertyViewingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PropertyViewing.objects.filter(customer=self.request.user).order_by('-scheduled_date')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePropertyViewingSerializer
        return PropertyViewingSerializer

    def perform_create(self, serializer):
        property_obj = get_object_or_404(Property, id=serializer.validated_data['property'].id)
        serializer.save(customer=self.request.user, property=property_obj)


class PropertyViewingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertyViewingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PropertyViewing.objects.filter(customer=self.request.user)


class CustomerFeedbackListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerFeedback.objects.filter(customer=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateCustomerFeedbackSerializer
        return CustomerFeedbackSerializer

    def perform_create(self, serializer):
        property_id = serializer.validated_data.get('property')
        property_obj = get_object_or_404(Property, id=property_id.id) if property_id else None
        serializer.save(customer=self.request.user, property=property_obj)


class CustomerFeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerFeedback.objects.filter(customer=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    saved_property, created = SavedProperty.objects.get_or_create(
        customer=request.user,
        property=property_obj,
        defaults={'notes': request.data.get('notes', '')}
    )
    
    if created:
        return Response({'message': 'Property saved successfully'}, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': 'Property already saved'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def unsave_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    try:
        saved_property = SavedProperty.objects.get(customer=request.user, property=property_obj)
        saved_property.delete()
        return Response({'message': 'Property removed from saved list'}, status=status.HTTP_200_OK)
    except SavedProperty.DoesNotExist:
        return Response({'error': 'Property not found in saved list'}, status=status.HTTP_404_NOT_FOUND)
