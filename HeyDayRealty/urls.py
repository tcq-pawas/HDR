# """
# URL configuration for HeyDayRealty project.

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/5.2/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static

# urlpatterns = [
#     # Smart dashboard entry point (must be first) - role-aware universal entry point
#     path('dashboard/', include('Apps.Administration.smart_dashboard_urls')),
    
#     # Authentication (must be first)
#     path('auth/', include(('Apps.Administration.auth_urls', 'auth'), namespace='auth')),
    
#     # Admin interface (Django admin)
#     path('django-admin/', admin.site.urls),
    
#     # Public-facing pages (view-only)
#     path('', include(('Apps.PublicPage.urls', 'public'), namespace='public')),
    
#     # Buy and Sell modules
#     path('buy/', include(('Apps.buy.urls', 'buy'), namespace='buy')),
#     path('sell/', include(('Apps.sell.urls', 'sell'), namespace='sell')),
    

#     path('public/', include('Apps.PublicPage.urls')),
    

    
#     # Agent Dashboard
#     path('agent/', include(('Apps.Agent.urls', 'agent'), namespace='agent')),
    
#     # Role-based dashboards (with unique prefixes and strict access control)
#     path('customer/', include(('Apps.Customer.urls', 'customer'), namespace='customer')),
#     path('investor/', include(('Apps.Investor.urls', 'investor'), namespace='investor')),
#     path('admin-dashboard/', include(('Apps.Administration.urls', 'admin_dash'), namespace='admin_dash')),
    
#     # API endpoints with role-based filtering
#     path('api/customer/', include(('Apps.Customer.urls', 'api_customer'), namespace='api_customer')),
#     path('api/investor/', include(('Apps.Investor.urls', 'api_investor'), namespace='api_investor')),
#     path('api/admin/', include(('Apps.Administration.urls', 'api_admin'), namespace='api_admin')),
#     path('api-auth/', include('rest_framework.urls')),
    
# ]

# # Custom error handlers for unauthorized access
# handler403 = 'Apps.Administration.auth_views.unauthorized_access'

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


"""
URL configuration for HeyDayRealty project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Smart dashboard entry point (must be first) - role-aware universal entry point
    path('dashboard/', include('Apps.Administration.smart_dashboard_urls')),
    
    # Authentication (must be first)
    path('auth/', include(('Apps.Administration.auth_urls', 'auth'), namespace='auth')),
    
    # Admin interface (Django admin)
    path('django-admin/', admin.site.urls),
    
    # Public-facing pages (view-only)
    path('', include(('Apps.PublicPage.urls', 'public'), namespace='public')),
    
    # Buy and Sell modules
    path('buy/', include(('Apps.buy.urls', 'buy'), namespace='buy')),
    path('sell/', include(('Apps.sell.urls', 'sell'), namespace='sell')),
    
    # Agent Dashboard
    path('agent/', include(('Apps.Agent.urls', 'agent'), namespace='agent')),
    
    # Role-based dashboards (with unique prefixes and strict access control)
    path('customer/', include(('Apps.Customer.urls', 'customer'), namespace='customer')),
    path('investor/', include(('Apps.Investor.urls', 'investor'), namespace='investor')),
    path('admin-dashboard/', include(('Apps.Administration.urls', 'admin_dash'), namespace='admin_dash')),
    
    # API endpoints with role-based filtering
    path('api/customer/', include(('Apps.Customer.urls', 'api_customer'), namespace='api_customer')),
    path('api/investor/', include(('Apps.Investor.urls', 'api_investor'), namespace='api_investor')),
    path('api/admin/', include(('Apps.Administration.urls', 'api_admin'), namespace='api_admin')),
    path('api-auth/', include('rest_framework.urls')),
    
]

# Custom error handlers for unauthorized access
handler403 = 'Apps.Administration.auth_views.unauthorized_access'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)