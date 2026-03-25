from django.urls import path
from .auth_views import CustomLoginView, CustomLogoutView, unauthorized_access

app_name = 'auth'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('unauthorized/', unauthorized_access, name='unauthorized'),
]
