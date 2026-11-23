import sys
import types
import django
from datetime import datetime

# Stub missing third-party deps
for name in ['storages', 'storages.backends', 'storages.backends.s3boto3']:
    sys.modules[name] = types.ModuleType(name)


class _S:
    def __init__(self, *a, **k):
        pass


sys.modules['storages.backends.s3boto3'].S3Boto3Storage = _S

from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.staticfiles',
        'Apps.PublicPage',
    ],
    DATABASES={},
    STATIC_URL='/static/',
    ROOT_URLCONF='_devin_test_urls',
    USE_TZ=True,
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'libraries': {'custom_tags': 'Apps.PublicPage.templatetags.custom_tags'},
            'context_processors': [],
        },
    }],
)
django.setup()

from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser

IMG = 'https://placehold.co/1200x800/0F6A3C/ffffff?text=Property'
THUMB = 'https://placehold.co/200x200/0F6A3C/ffffff?text=Thumb'


class Img:
    def __init__(self, url):
        self.url = url


class GalleryImage:
    def __init__(self, url):
        self.image = Img(url)


class FakeQS(list):
    @property
    def count(self):
        return len(self)

    @property
    def first(self):
        return self[0] if self else None

    def all(self):
        return self


class AgentProfile:
    is_verified = True
    masked_phone = '+91 ******1234'
    masked_email = 'a***@example.com'
    phone = '919876543210'
    profile_picture = None


class UserSubscription:
    status = 'active'

    class plan:
        name = 'Gold'
        badge_image = None


class Seller:
    username = 'agent_rao'
    first_name = 'Ravi'
    last_name = 'Kumar'
    agent_profile = AgentProfile()
    user_subscription = None

    def get_full_name(self):
        return 'Ravi Kumar'


class Property:
    id = 42
    title = 'Premium Agricultural Land - 5 Acres Near Bangalore'
    seo_title = ''
    seo_description = ''
    public_description = 'Excellent agricultural land with clear title, road connectivity, water availability and fertile soil. Ideal for farming and long-term investment.'
    description = ''
    created_at = datetime(2026, 11, 10)
    price = 4500000
    location = 'Devanahalli, Bangalore Rural, Karnataka'
    total_area = 5
    area_unit = 'acre'
    plot_area = None
    area_sqft = None
    project_size_acre = 5
    category = 'agricultural_land'
    land_shape = 'rectangular'
    ownership_type = 'freehold'
    road_width = 30
    road_access = ''
    road_connectivity = ''
    water_source = 'Borewell'
    soil_type = 'Red Loamy'
    google_map_link = ''
    featured_image = Img(IMG)
    images = FakeQS([GalleryImage(THUMB + '?text=1'), GalleryImage(THUMB + '?text=2'),
                     GalleryImage(THUMB + '?text=3'), GalleryImage(THUMB + '?text=4')])
    seller = Seller()

    def get_category_display(self):
        return 'Agricultural Land'

    def get_area_unit_display(self):
        return 'Acres'

    def get_land_shape_display(self):
        return 'Rectangular'

    def get_ownership_type_display(self):
        return 'Freehold'


class Field:
    def __init__(self, id_):
        self.id_for_label = id_
        self.errors = []

    def __str__(self):
        return '<input type="text">'


class Form:
    name = Field('id_name')
    email = Field('id_email')
    message = Field('id_message')


class Req:
    scheme = 'http'

    def get_host(self):
        return 'localhost:8765'

    def build_absolute_uri(self):
        return 'http://localhost:8765/buy/42/'


prop = Property()
similar = Property()
similar.id = 43
similar.title = 'Farm Plot - 2 Acres Near Hosur'
similar.price = 1800000
similar.location = 'Hosur, Tamil Nadu'

html = render_to_string('buy/property_detail.html', {
    'property': prop,
    'similar_properties': [similar, similar, similar],
    'is_saved': False,
    'form': Form(),
    'user': AnonymousUser(),
    'request': Req(),
})

with open('_preview_property_detail.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('written', len(html))
