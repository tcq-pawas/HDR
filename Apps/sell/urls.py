from django.urls import path
from . import views

app_name = 'sell'

urlpatterns = [
    path('', views.sell_page, name='sell_page'),
    path('dashboard/', views.property_list, name='property_list'),
    path('create/', views.property_create, name='property_create'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('<int:pk>/edit/', views.property_update, name='property_update'),
    path('<int:pk>/delete/', views.property_delete, name='property_delete'),
]
