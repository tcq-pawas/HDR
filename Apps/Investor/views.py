from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    InvestorProfile, InvestmentListing, Investment, ROIData,
    InvestorDocument, InvestorMeeting
)
from .serializers import (
    InvestorProfileSerializer, InvestmentListingSerializer, InvestmentSerializer,
    ROIDataSerializer, InvestorDocumentSerializer, InvestorMeetingSerializer,
    CreateInvestmentSerializer, CreateInvestorDocumentSerializer,
    CreateInvestorMeetingSerializer, UpdateInvestmentStatusSerializer,
    UpdateROIDataSerializer
)


class InvestorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = InvestorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = InvestorProfile.objects.get_or_create(user=self.request.user)
        return profile


class InvestmentListingListView(generics.ListAPIView):
    serializer_class = InvestmentListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['investment_type', 'status', 'property__property_type']
    search_fields = ['title', 'description', 'property__title', 'property__location']
    ordering_fields = ['created_at', 'expected_roi_percentage', 'total_investment_needed']
    ordering = ['-created_at']

    def get_queryset(self):
        return InvestmentListing.objects.filter(status='active').select_related('property')


class InvestmentListingDetailView(generics.RetrieveAPIView):
    serializer_class = InvestmentListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvestmentListing.objects.select_related('property')


class InvestmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Investment.objects.filter(investor=self.request.user).select_related(
            'listing', 'listing__property'
        ).order_by('-investment_date')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvestmentSerializer
        return InvestmentSerializer

    def perform_create(self, serializer):
        listing = get_object_or_404(InvestmentListing, id=serializer.validated_data['listing'].id)
        serializer.save(investor=self.request.user, listing=listing)


class InvestmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Investment.objects.filter(investor=self.request.user).select_related(
            'listing', 'listing__property'
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_investment_status(request, investment_id):
    investment = get_object_or_404(Investment, id=investment_id, investor=request.user)
    serializer = UpdateInvestmentStatusSerializer(investment, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ROIDataListView(generics.ListAPIView):
    serializer_class = ROIDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ROIData.objects.filter(
            investment__investor=self.request.user
        ).select_related('investment', 'investment__listing', 'investment__listing__property')


class ROIDataDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ROIDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ROIData.objects.filter(
            investment__investor=self.request.user
        ).select_related('investment', 'investment__listing', 'investment__listing__property')


class InvestorDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvestorDocument.objects.filter(investor=self.request.user).order_by('-uploaded_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvestorDocumentSerializer
        return InvestorDocumentSerializer

    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)


class InvestorDocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = InvestorDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvestorDocument.objects.filter(investor=self.request.user)


class InvestorMeetingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvestorMeeting.objects.filter(investor=self.request.user).order_by('-scheduled_date')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvestorMeetingSerializer
        return InvestorMeetingSerializer

    def perform_create(self, serializer):
        serializer.save(investor=self.request.user)


class InvestorMeetingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvestorMeetingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvestorMeeting.objects.filter(investor=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investment_dashboard(request):
    investor = request.user
    investments = Investment.objects.filter(investor=investor)
    
    total_invested = investments.aggregate(total=Sum('amount'))['total'] or 0
    total_investments = investments.count()
    
    # Calculate portfolio breakdown
    portfolio_breakdown = investments.values(
        'listing__investment_type'
    ).annotate(
        amount=Sum('amount'),
        count=Count('id')
    ).order_by('-amount')
    
    # Recent investments
    recent_investments = investments.select_related(
        'listing', 'listing__property'
    ).order_by('-investment_date')[:5]
    
    # ROI data
    roi_data = ROIData.objects.filter(
        investment__investor=investor
    ).select_related('investment')
    
    total_returns = roi_data.aggregate(
        total=Sum('total_returns')
    )['total'] or 0
    
    data = {
        'total_invested': total_invested,
        'total_investments': total_investments,
        'total_returns': total_returns,
        'portfolio_breakdown': list(portfolio_breakdown),
        'recent_investments': InvestmentSerializer(recent_investments, many=True).data,
        'roi_summary': ROIDataSerializer(roi_data, many=True).data,
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def featured_investments(request):
    listings = InvestmentListing.objects.filter(
        featured=True,
        status='active'
    ).select_related('property').order_by('-created_at')
    
    serializer = InvestmentListingSerializer(listings, many=True)
    return Response(serializer.data)
