from types import SimpleNamespace

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Property
from Apps.Agent.models import AgentProfile


def _canonical_site():
    """Force sitemap URLs onto the production canonical host."""
    return SimpleNamespace(
        domain=getattr(settings, "SITE_CANONICAL_HOST", "hhectare.com"),
        name=getattr(settings, "SITE_NAME", "HHectare"),
    )


class CanonicalSitemap(Sitemap):
    protocol = "https"

    def get_urls(self, page=1, site=None, protocol=None):
        return super().get_urls(
            page=page,
            site=_canonical_site(),
            protocol="https",
        )


class PropertySitemap(CanonicalSitemap):
    """Sitemap for Property listings - includes only public, approved properties"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Property.objects.filter(
            is_active=True,
            status="approved",
            show_to_public=True,
            is_admin_list=False,
        ).select_related("seller")

    def lastmod(self, obj):
        return obj.updated_at


class AgentProfileSitemap(CanonicalSitemap):
    """Sitemap for Agent Profiles - includes only verified agents"""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return AgentProfile.objects.filter(
            is_verified=True,
            user__is_active=True,
        ).select_related("user")

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(CanonicalSitemap):
    """Sitemap for public marketing pages"""
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return [
            ("public:home", 1.0, "daily"),
            ("public:about", 0.8, "monthly"),
            ("public:contact", 0.7, "monthly"),
            ("public:career", 0.5, "monthly"),
            ("public:nri", 0.6, "monthly"),
            ("public:property_list", 0.8, "daily"),
            ("public:agents", 0.6, "weekly"),
            ("public:subscription_plans", 0.5, "weekly"),
            ("public:property_management", 0.5, "monthly"),
            ("public:blogs", 0.5, "weekly"),
            ("buy:property_search", 0.9, "daily"),
            ("sell:sell_page", 0.6, "monthly"),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]

    def changefreq(self, item):
        return item[2]
