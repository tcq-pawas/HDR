from django.db import models
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property


class InvestorProfile(models.Model):
    INVESTOR_TYPES = [
        ('individual', 'Individual'),
        ('corporate', 'Corporate'),
        ('institutional', 'Institutional'),
        ('partnership', 'Partnership'),
    ]
    
    RISK_TOLERANCE = [
        ('conservative', 'Conservative'),
        ('moderate', 'Moderate'),
        ('aggressive', 'Aggressive'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='investor_profile')
    investor_type = models.CharField(max_length=20, choices=INVESTOR_TYPES, default='individual')
    company_name = models.CharField(max_length=200, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    risk_tolerance = models.CharField(max_length=20, choices=RISK_TOLERANCE, default='moderate')
    investment_range_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    investment_range_max = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    preferred_property_types = models.CharField(max_length=500, blank=True, null=True, help_text="Comma-separated list")
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Investor Profile"


class InvestmentListing(models.Model):
    LISTING_STATUS = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    INVESTMENT_TYPE = [
        ('equity', 'Equity'),
        ('debt', 'Debt'),
        ('hybrid', 'Hybrid'),
        ('crowdfunding', 'Crowdfunding'),
    ]
    
    property_obj = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='investment_listings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPE, default='equity')
    total_investment_needed = models.DecimalField(max_digits=15, decimal_places=2)
    minimum_investment = models.DecimalField(max_digits=12, decimal_places=2)
    expected_roi_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual ROI percentage")
    investment_term_months = models.IntegerField(help_text="Investment duration in months")
    status = models.CharField(max_length=20, choices=LISTING_STATUS, default='active')
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closes_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.property_obj.title}"

    @property
    def total_invested_amount(self):
        return self.investments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    @property
    def investment_percentage_filled(self):
        if self.total_investment_needed > 0:
            return (self.total_invested_amount / self.total_investment_needed) * 100
        return 0


class Investment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    listing = models.ForeignKey(InvestmentListing, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    investment_date = models.DateTimeField(auto_now_add=True)
    confirmed_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['investor', 'listing']

    def __str__(self):
        return f"{self.investor.username} invested ${self.amount} in {self.listing.title}"


class ROIData(models.Model):
    investment = models.OneToOneField(Investment, on_delete=models.CASCADE, related_name='roi_data')
    actual_roi_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    total_returns = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    last_payment_date = models.DateTimeField(blank=True, null=True)
    next_payment_date = models.DateTimeField(blank=True, null=True)
    payment_frequency = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually')],
        default='monthly'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ROI Data for {self.investment}"


class InvestorDocument(models.Model):
    DOCUMENT_TYPES = [
        ('kyc', 'KYC Document'),
        ('financial', 'Financial Statement'),
        ('agreement', 'Investment Agreement'),
        ('verification', 'Verification Document'),
        ('other', 'Other'),
    ]
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investor_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='investor_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='verified_documents')
    verified_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.investor.username} - {self.title}"


class InvestorMeeting(models.Model):
    MEETING_TYPES = [
        ('consultation', 'Consultation'),
        ('presentation', 'Investment Presentation'),
        ('due_diligence', 'Due Diligence'),
        ('closing', 'Deal Closing'),
        ('follow_up', 'Follow Up'),
    ]
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investor_meetings')
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=200, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='scheduled'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.investor.username} - {self.title}"
