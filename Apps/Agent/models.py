from django.db import models
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property

class AgentProfile(models.Model):
    """Extended profile for agents/sellers"""

    VERIFICATION_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    
    phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True, help_text="Alternate contact number")
    company_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='agent_profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    employee_id = models.CharField(max_length=50, blank=True)
    territory = models.CharField(max_length=200, blank=True, help_text="Assigned territory/region")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.5, help_text="Commission percentage")
    target_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monthly sales target")
    notification_email = models.BooleanField(default=True)
    notification_sms = models.BooleanField(default=False)
    notification_whatsapp = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_proof_document = models.FileField(upload_to='agent_verification/id_proof/', blank=True, null=True)
    address_proof_document = models.FileField(upload_to='agent_verification/address_proof/', blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='not_started')
    verification_remarks = models.TextField(blank=True, null=True)
    # Contact Information
    address = models.TextField(blank=True, help_text="Full address")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)


    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Agent"

    def masked_phone(self):
        if not self.phone:
            return ""

        phone = str(self.phone)

        if len(phone) <= 4:
            return phone

        return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


    def masked_email(self):
        email = self.user.email

        if not email or "@" not in email:
            return ""

        username, domain = email.split("@", 1)

        if len(username) <= 2:
            masked_username = username[0] + "*" * (len(username) - 1)
        else:
            masked_username = username[:2] + "X" * (len(username) - 2)

        return f"{masked_username}@{domain}"

    class Meta:
        verbose_name = "Agent Profile"
        verbose_name_plural = "Agent Profiles"

    def get_absolute_url(self):
        """Return the absolute URL for this agent profile"""
        from django.urls import reverse
        return reverse('public:agent_profile', kwargs={'agent_id': self.id})


class Lead(models.Model):
    """Lead management for agents"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal Sent'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ]
    
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('social_media', 'Social Media'),
        ('advertisement', 'Advertisement'),
        ('cold_call', 'Cold Call'),
        ('walk_in', 'Walk In'),
        ('other', 'Other'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leads')
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='website')
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')
    expected_close_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.status}"

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ['-created_at']


class LeadFollowUp(models.Model):
    """Track follow-ups for leads"""
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    agent = models.ForeignKey(User, on_delete=models.CASCADE)
    follow_up_type = models.CharField(max_length=20, choices=[
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('meeting', 'Meeting'),
        ('site_visit', 'Site Visit'),
        ('other', 'Other'),
    ])
    notes = models.TextField()
    scheduled_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Follow-up for {self.lead.name} - {self.follow_up_type}"

    class Meta:
        verbose_name = "Lead Follow-up"
        verbose_name_plural = "Lead Follow-ups"
        ordering = ['-scheduled_date']


class SiteVisit(models.Model):
    """Site visit scheduling and management"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='site_visits')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='site_visits')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='site_visits')
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Site visit for {self.property.title} on {self.scheduled_date}"

    class Meta:
        verbose_name = "Site Visit"
        verbose_name_plural = "Site Visits"
        ordering = ['-scheduled_date']


class Booking(models.Model):
    """Booking and sales management"""
    
    STATUS_CHOICES = [
        ('token_paid', 'Token Paid'),
        ('agreement_signed', 'Agreement Signed'),
        ('installment_pending', 'Installment Pending'),
        ('installment_completed', 'Installment Completed'),
        ('payment_completed', 'Payment Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='token_paid')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    token_amount = models.DecimalField(max_digits=12, decimal_places=2)
    token_paid_date = models.DateTimeField(null=True, blank=True)
    agreement_signed_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking for {self.property.title} - {self.customer_name}"

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-booking_date']


class Installment(models.Model):
    """Installment tracking for bookings"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Installment {self.installment_number} for {self.booking}"

    class Meta:
        verbose_name = "Installment"
        verbose_name_plural = "Installments"
        ordering = ['installment_number']


class Commission(models.Model):
    """Commission tracking for agents"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commissions')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='commissions')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='commissions')
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    sale_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commission for {self.agent.username} - ₹{self.commission_amount}"

    class Meta:
        verbose_name = "Commission"
        verbose_name_plural = "Commissions"
        ordering = ['-created_at']


class Document(models.Model):
    """Document management for properties and customers"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('property', 'Property Document'),
        ('customer', 'Customer Document'),
        ('agreement', 'Agreement'),
        ('receipt', 'Receipt'),
        ('other', 'Other'),
    ]
    
    CATEGORY_CHOICES = [
        ('title_deed', 'Title Deed'),
        ('approval', 'Approval Document'),
        ('tax', 'Tax Document'),
        ('identity', 'Identity Proof'),
        ('address', 'Address Proof'),
        ('photograph', 'Photograph'),
        ('other', 'Other'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/')
    file_size = models.BigIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.document_type}"

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-uploaded_at']


class VerificationDocument(models.Model):
    """KYC / identity documents submitted by agents for admin verification."""

    DOCUMENT_TYPE_CHOICES = [
        ('aadhaar', 'Aadhaar Card'),
        ('pan', 'PAN Card'),
        ('voter_id', 'Voter ID'),
        ('driving_license', 'Driving License'),
        ('passport', 'Passport'),
        ('address_proof', 'Address Proof'),
        ('bank_statement', 'Bank Statement'),
        ('gst_certificate', 'GST Certificate'),
        ('other', 'Other'),
    ]

    # Types the platform requires before overall verification can complete
    REQUIRED_DOCUMENT_TYPES = ('aadhaar', 'pan', 'address_proof')

    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('reupload_required', 'Re-upload Required'),
    ]

    agent = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='verification_documents'
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_name = models.CharField(
        max_length=200, blank=True,
        help_text="Custom name when document type is Other"
    )
    front_file = models.FileField(upload_to='agent_verification/front/')
    back_file = models.FileField(upload_to='agent_verification/back/', blank=True, null=True)
    has_back_side = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending_review'
    )
    rejection_reason = models.TextField(blank=True)
    admin_reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_verification_documents'
    )
    admin_reviewed_at = models.DateTimeField(null=True, blank=True)
    replaces = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='replacements',
        help_text="Previous submission this re-upload replaces"
    )
    is_current = models.BooleanField(
        default=True,
        help_text="False for historical submissions kept after re-upload"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Verification Document"
        verbose_name_plural = "Verification Documents"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.display_name} ({self.get_status_display()}) - {self.agent}"

    @property
    def display_name(self):
        if self.document_type == 'other' and self.document_name:
            return self.document_name
        return self.get_document_type_display()

    @property
    def is_required_type(self):
        return self.document_type in self.REQUIRED_DOCUMENT_TYPES

    @property
    def can_reupload(self):
        return self.status in ('rejected', 'reupload_required')

    @classmethod
    def required_types(cls):
        return [
            {'code': code, 'label': label, 'required': True}
            for code, label in cls.DOCUMENT_TYPE_CHOICES
            if code in cls.REQUIRED_DOCUMENT_TYPES
        ]

    @classmethod
    def additional_types(cls):
        return [
            {'code': code, 'label': label, 'required': False}
            for code, label in cls.DOCUMENT_TYPE_CHOICES
            if code not in cls.REQUIRED_DOCUMENT_TYPES
        ]

    @classmethod
    def sync_agent_profile_status(cls, agent):
        """Derive AgentProfile.verification_status from current verification docs."""
        try:
            profile = agent.agent_profile
        except AgentProfile.DoesNotExist:
            return None

        current_docs = cls.objects.filter(agent=agent, is_current=True)
        if not current_docs.exists():
            profile.verification_status = 'not_started'
            profile.is_verified = False
            profile.save(update_fields=['verification_status', 'is_verified', 'updated_at'])
            return profile

        required_verified = all(
            current_docs.filter(document_type=code, status='verified').exists()
            for code in cls.REQUIRED_DOCUMENT_TYPES
        )
        has_actionable = current_docs.filter(
            status__in=['rejected', 'reupload_required']
        ).exists()
        has_pending = current_docs.filter(
            status__in=['pending_review', 'under_review']
        ).exists()

        if required_verified:
            profile.verification_status = 'approved'
            profile.is_verified = True
        elif has_actionable and not has_pending:
            profile.verification_status = 'rejected'
            profile.is_verified = False
            # Prefer latest rejection reason
            latest_reject = current_docs.filter(
                status__in=['rejected', 'reupload_required']
            ).exclude(rejection_reason='').order_by('-updated_at').first()
            if latest_reject:
                profile.verification_remarks = latest_reject.rejection_reason
        else:
            profile.verification_status = 'pending'
            profile.is_verified = False

        profile.save(update_fields=[
            'verification_status', 'is_verified', 'verification_remarks', 'updated_at'
        ])
        return profile


class Communication(models.Model):
    """Communication tracking (WhatsApp, Email, SMS)"""
    
    COMMUNICATION_TYPE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('call', 'Phone Call'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communications')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    recipient = models.CharField(max_length=100)  # Phone or email
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    template_used = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.communication_type} to {self.recipient}"

    class Meta:
        verbose_name = "Communication"
        verbose_name_plural = "Communications"
        ordering = ['-sent_at']


class MessageTemplate(models.Model):
    """Message templates for quick communication"""

    TEMPLATE_TYPE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]

    PURPOSE_CHOICES = [
        ('lead_followup', 'Lead Follow-up'),
        ('site_visit_reminder', 'Site Visit Reminder'),
        ('booking_confirmation', 'Booking Confirmation'),
        ('payment_reminder', 'Payment Reminder'),
        ('greeting', 'Greeting'),
        ('promotion', 'Promotion'),
        ('other', 'Other'),
    ]

    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_templates')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES, default='other')
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    variables = models.JSONField(default=dict, blank=True, help_text="Available variables for template")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.template_type}"

    class Meta:
        verbose_name = "Message Template"
        verbose_name_plural = "Message Templates"
        ordering = ['name']


class AgentReview(models.Model):
    """Reviews submitted by users for agents"""

    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer_name = models.CharField(max_length=100, help_text="Name of the reviewer")
    reviewer_email = models.EmailField(blank=True, help_text="Email of the reviewer (optional)")
    reviewer_phone = models.CharField(max_length=20, blank=True, help_text="Phone of the reviewer (optional)")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, help_text="Star rating (1-5)")
    review_text = models.TextField(help_text="Review description/thoughts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.reviewer_name} for {self.agent.user.get_full_name()} - {self.rating} stars"

    class Meta:
        verbose_name = "Agent Review"
        verbose_name_plural = "Agent Reviews"
        ordering = ['-created_at']
