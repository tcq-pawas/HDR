from django.db import models
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property
from Apps.Agent.models import Lead


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='customer_profiles/', blank=True, null=True)
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('phone', 'Phone'), ('both', 'Both')],
        default='email'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Customer Profile"


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='customer_inquiries', blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Inquiry from {self.customer.username}: {self.subject}"


class SavedProperty(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['customer', 'property']

    def __str__(self):
        return f"{self.customer.username} saved {self.property.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Automatically create lead when property is saved to wishlist
        if is_new:
            self._create_lead()

    def _create_lead(self):
        """Automatically create a lead for the property seller when customer saves property"""
        from Apps.Agent.models import Lead
        
        # Check if property has a seller
        if self.property.seller:
            # Check if lead already exists for this customer-property-agent combination
            existing_lead = Lead.objects.filter(
                agent=self.property.seller,
                property=self.property,
                email=self.customer.email,
                phone=self.customer.customer_profile.phone if hasattr(self.customer, 'customer_profile') else ''
            ).first()
            
            if not existing_lead:
                # Create new lead
                Lead.objects.create(
                    agent=self.property.seller,
                    property=self.property,
                    name=self.customer.get_full_name() or self.customer.username,
                    email=self.customer.email,
                    phone=self.customer.customer_profile.phone if hasattr(self.customer, 'customer_profile') else '',
                    source='website',
                    status='new',
                    notes=f'Lead generated from wishlist/favorite - Customer saved property to wishlist'
                )


class PropertyViewing(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_viewings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='viewings')
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Viewing of {self.property.title} by {self.customer.username}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Automatically create lead when property viewing is scheduled
        if is_new:
            self._create_lead()

    def _create_lead(self):
        """Automatically create a lead for the property seller when customer schedules viewing"""
        from Apps.Agent.models import Lead
        
        # Check if property has a seller
        if self.property.seller:
            # Check if lead already exists for this customer-property-agent combination
            existing_lead = Lead.objects.filter(
                agent=self.property.seller,
                property=self.property,
                email=self.customer.email,
                phone=self.customer.customer_profile.phone if hasattr(self.customer, 'customer_profile') else ''
            ).first()
            
            if not existing_lead:
                # Create new lead
                Lead.objects.create(
                    agent=self.property.seller,
                    property=self.property,
                    name=self.customer.get_full_name() or self.customer.username,
                    email=self.customer.email,
                    phone=self.customer.customer_profile.phone if hasattr(self.customer, 'customer_profile') else '',
                    source='website',
                    status='new',
                    notes=f'Lead generated from property viewing - Customer scheduled property visit for {self.scheduled_date}'
                )


class CustomerFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='feedback', blank=True, null=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        property_name = self.property.title if self.property else "General"
        return f"Feedback for {property_name} by {self.customer.username}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=SavedProperty)
def create_lead_on_save(sender, instance, created, **kwargs):
    """
    Automatically generate a Lead for the assigned agent when a customer saves a property.
    """
    agent = instance.property.assigned_agent or instance.property.seller
    
    if created and agent:
        from Apps.Agent.models import Lead
        
        customer = instance.customer
        customer_name = customer.get_full_name() or customer.username
        customer_email = customer.email
        customer_phone = ""
        
        # Try to get phone from CustomerProfile
        if hasattr(customer, 'customer_profile') and customer.customer_profile.phone:
            customer_phone = customer.customer_profile.phone
            
        # Create Lead
        Lead.objects.get_or_create(
            agent=agent,
            property=instance.property,
            email=customer_email,
            defaults={
                'name': customer_name,
                'phone': customer_phone,
                'status': 'new',
                'source': 'website',
                'notes': f"Lead auto-generated from customer {customer_name} saving property '{instance.property.title}' to their wishlist."
            }
        )

