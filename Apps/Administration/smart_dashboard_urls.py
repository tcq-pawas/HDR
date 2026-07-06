from django.urls import path
from .smart_dashboard_views import SmartDashboardRedirectView

app_name = 'smart_dashboard'

urlpatterns = [
    path('', SmartDashboardRedirectView.as_view(), name='redirect'),
]
