from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Property
from Apps.Agent.models import AgentProfile
from django.utils import timezone


class PropertySitemap(Sitemap):
    """Sitemap for Property listings - includes only public, approved properties"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        """Return all active, approved properties that are visible to public"""
        return Property.objects.filter(
            is_active=True,
            status='approved',
            show_to_public=True,
            is_admin_list=False
        ).select_related('seller').prefetch_related('images')

    def lastmod(self, obj):
        """Return the last modified date"""
        return obj.updated_at


class AgentProfileSitemap(Sitemap):
    """Sitemap for Agent Profiles - includes only verified agents"""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        """Return all verified agent profiles"""
        return AgentProfile.objects.filter(
            is_verified=True,
            user__is_active=True
        ).select_related('user')

    def lastmod(self, obj):
        """Return the last modified date"""
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        """Return static page names"""
        return [
            'public:home',
            'public:about',
            'public:contact',
            'public:career',
            'public:nri',
            'public:property_list',
            'public:agents',
            'public:subscription_plans',
            'buy:property_search',
            'sell:sell_page',
        ]

    def location(self, item):
        """Return URL for each static page"""
        return reverse(item)
