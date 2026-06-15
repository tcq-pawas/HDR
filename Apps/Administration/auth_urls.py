from django.urls import path, include
from django.contrib.auth import views as auth_views
from .auth_views import CustomLoginView, CustomLogoutView, unauthorized_access, CustomerRegistrationView, PartnerRegistrationView

app_name = 'auth'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/customer/', CustomerRegistrationView.as_view(), name='register_customer'),
    path('register/partner/', PartnerRegistrationView.as_view(), name='register_partner'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('unauthorized/', unauthorized_access, name='unauthorized'),
    
    # Override password reset confirm and complete to fix namespace and use custom templates
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/auth/reset/done/'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
         
    path('', include('django.contrib.auth.urls')),
]
