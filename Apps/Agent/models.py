from django.db import models
from django.contrib.auth.models import User
from Apps.PublicPage.models import Property


class AgentProfile(models.Model):
    """Extended profile for agents/sellers"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='agent_profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Agent"

    class Meta:
        verbose_name = "Agent Profile"
        verbose_name_plural = "Agent Profiles"


class PropertyInquiry(models.Model):
    """Track inquiries received for properties"""
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='agent_inquiries'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry from {self.name} for {self.property.title}"

    class Meta:
        verbose_name = "Property Inquiry"
        verbose_name_plural = "Property Inquiries"
        ordering = ['-created_at']
