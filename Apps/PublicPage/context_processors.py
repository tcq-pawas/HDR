"""SEO defaults available to every public template."""

from django.conf import settings
from django.templatetags.static import static


def seo_defaults(request):
    origin = getattr(settings, "SITE_CANONICAL_ORIGIN", "https://hhectare.com").rstrip("/")
    path = request.path if request else "/"
    logo_path = static("img/logo.png")
    logo_url = f"{origin}{logo_path}" if logo_path.startswith("/") else f"{origin}/{logo_path}"

    return {
        "site_name": getattr(settings, "SITE_NAME", "HHectare"),
        "site_slogan": getattr(settings, "SITE_SLOGAN", "Invest Green. Grow Strong."),
        "site_description": getattr(
            settings,
            "SITE_DESCRIPTION",
            "HHectare is a premium farmland and real estate investment platform in India.",
        ),
        "seo_origin": origin,
        "seo_canonical": f"{origin}{path}",
        "seo_logo_url": logo_url,
        "seo_email": getattr(settings, "SITE_CONTACT_EMAIL", "info@hhectare.com"),
        "seo_phone": getattr(settings, "SITE_CONTACT_PHONE", "+919506688688"),
        "seo_phone_display": getattr(settings, "SITE_CONTACT_PHONE_DISPLAY", "+91 95066 88688"),
        "seo_same_as": getattr(settings, "SITE_SAME_AS", []),
    }
