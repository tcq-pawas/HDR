from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from .models import CustomerProfile, Inquiry, SavedProperty, CustomerFeedback
from .serializers import (
    CustomerProfileSerializer, InquirySerializer, SavedPropertySerializer,
    CustomerFeedbackSerializer,
    CreateInquirySerializer, CreateSavedPropertySerializer,
    CreateCustomerFeedbackSerializer
)
from Apps.PublicPage.models import Property
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from .forms import CreatePropertyInquiryForm
from Apps.Agent.models import AgentProfile
from django.db import models





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


def create_inquiry(request):
    """
    Renders the 'Connect with a Property Expert' form (GET)
    and saves a PropertyInquiry record on submit (POST).
    """
    if request.method == 'POST':
        form = CreatePropertyInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            # Link the logged-in customer's email automatically if not provided
            if not inquiry.email and request.user.is_authenticated:
                inquiry.email = request.user.email
            inquiry.save()
            messages.success(request, "Your enquiry has been submitted successfully. Our property expert will get back to you shortly.")
            return redirect('customer:inquiries-page')
        else:
            messages.error(request, "Please correct the errors below and try again.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['name'] = request.user.get_full_name() or request.user.username
            initial['email'] = request.user.email
        form = CreatePropertyInquiryForm(initial=initial)
 
    return render(request, "customer/create_inquiry.html", {"form": form})



#  get_advisor_properties function :
def get_advisor_properties(request, agent_profile_id):
    
    try:
        agent_profile = AgentProfile.objects.select_related('user').get(id=agent_profile_id)
    except AgentProfile.DoesNotExist:
        return JsonResponse({'error': 'Advisor not found'}, status=404)

    properties = Property.objects.filter(
        is_active=True
    ).filter(
        models.Q(assigned_agent=agent_profile.user) | models.Q(seller=agent_profile.user)
    )

    properties_data = []
    for p in properties:
        properties_data.append({
            'id': p.id,
            'title': p.title,
            'location': p.location,
            'category': p.get_category_display() if hasattr(p, 'get_category_display') else p.category,
            'price': f"₹{p.price:,.0f}" if p.price else "Contact for price",
            'image_url': p.featured_image.url if p.featured_image else (
                p.images.first().image.url if p.images.exists() else None
            ),
        })

    return JsonResponse({
        'service_area': agent_profile.territory or 'Not specified',
        'advisor_name': agent_profile.user.get_full_name() or agent_profile.user.username,
        'properties': properties_data,
    })
    
    
