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
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    risk_tolerance = models.CharField(max_length=20, choices=RISK_TOLERANCE, default='moderate')
    investment_range_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    investment_range_max = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    min_investment_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    max_investment_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    preferred_property_types = models.CharField(max_length=500, blank=True, null=True, help_text="Comma-separated list")
    preferred_investment_type = models.CharField(max_length=20, blank=True, null=True)
    investment_duration = models.CharField(max_length=20, blank=True, null=True)
    investment_goals = models.TextField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    
    # KYC and Tax Information
    pan_number = models.CharField(max_length=20, blank=True, null=True, help_text="Permanent Account Number")
    kyc_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('submitted', 'Submitted'), ('verified', 'Verified'), ('rejected', 'Rejected')],
        default='pending'
    )
    kyc_document = models.FileField(upload_to='kyc_documents/', blank=True, null=True)
    kyc_verified_at = models.DateTimeField(blank=True, null=True)
    
    # Bank Information
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    bank_account_type = models.CharField(
        max_length=20,
        choices=[('savings', 'Savings'), ('current', 'Current')],
        blank=True, null=True
    )
    
    # Tax Information
    tax_residency = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True, help_text="Tax identification number")
    
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
    
    # Performance tracking
    current_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Current value of investment")
    profit_loss = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Profit or loss amount")
    profit_loss_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Profit/loss percentage")
    last_valuation_date = models.DateTimeField(blank=True, null=True, help_text="Date of last valuation update")
    exit_date = models.DateTimeField(blank=True, null=True, help_text="Date when investment was exited")
    exit_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Value at exit")

    class Meta:
        unique_together = ['investor', 'listing']

    def __str__(self):
        return f"{self.investor.username} invested ${self.amount} in {self.listing.title}"


class InvestmentRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('admin_reviewed', 'Admin Reviewed'),
        ('agent_assigned', 'Agent Assigned'),
        ('document_verified', 'Document Verified'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_requests')
    listing = models.ForeignKey(InvestmentListing, on_delete=models.CASCADE, related_name='investment_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    agent_assigned = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_requests')
    document_verification_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')],
        default='pending'
    )
    investment = models.OneToOneField(Investment, on_delete=models.SET_NULL, blank=True, null=True, related_name='request')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['investor', 'listing']

    def __str__(self):
        return f"{self.investor.username} - ${self.amount} request for {self.listing.title} ({self.status})"


class PropertyValuation(models.Model):
    VALUATION_METHODS = [
        ('comparative', 'Comparative Market Analysis'),
        ('income', 'Income Capitalization'),
        ('cost', 'Cost Approach'),
        ('professional', 'Professional Appraisal'),
    ]
    
    property_obj = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='valuations')
    valuation_date = models.DateField(help_text="Date of valuation")
    current_value = models.DecimalField(max_digits=15, decimal_places=2, help_text="Current market value")
    appreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Annual appreciation rate percentage")
    valuation_method = models.CharField(max_length=20, choices=VALUATION_METHODS, default='comparative')
    valuator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='property_valuations')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-valuation_date']
        unique_together = ['property_obj', 'valuation_date']

    def __str__(self):
        return f"{self.property_obj.title} - ${self.current_value} ({self.valuation_date})"


class ROIHistory(models.Model):
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='roi_history')
    record_date = models.DateField(help_text="Date of ROI record")
    roi_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="ROI percentage at this point")
    cumulative_returns = models.DecimalField(max_digits=15, decimal_places=2, help_text="Cumulative returns to date")
    monthly_return = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Return for this month")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-record_date']
        unique_together = ['investment', 'record_date']

    def __str__(self):
        return f"{self.investment} - {self.roi_percentage}% on {self.record_date}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('appreciation_alert', 'Property Appreciation Alert'),
        ('investment_update', 'Investment Update'),
        ('document_update', 'Document Update'),
        ('new_opportunity', 'New Investment Opportunity'),
        ('admin_message', 'Admin Message'),
        ('request_approved', 'Investment Request Approved'),
        ('request_rejected', 'Investment Request Rejected'),
        ('payment_received', 'Payment Received'),
        ('roi_update', 'ROI Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investor_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Optional related objects
    related_investment = models.ForeignKey(Investment, on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications')
    related_listing = models.ForeignKey(InvestmentListing, on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications')
    related_document = models.ForeignKey('InvestorDocument', on_delete=models.SET_NULL, blank=True, null=True, related_name='notifications')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class InvestmentReport(models.Model):
    REPORT_TYPES = [
        ('portfolio', 'Portfolio Report'),
        ('investment', 'Investment Report'),
        ('roi', 'ROI Report'),
        ('tax', 'Tax Report'),
        ('annual', 'Annual Report'),
    ]
    
    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    report_format = models.CharField(max_length=10, choices=REPORT_FORMATS, default='pdf')
    title = models.CharField(max_length=200)
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(blank=True, null=True)
    file_path = models.FileField(upload_to='investment_reports/', blank=True, null=True)
    data_snapshot = models.JSONField(blank=True, null=True, help_text="Snapshot of data at report generation time")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='generated_reports')

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.investor.username} - {self.title} ({self.report_type})"


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
