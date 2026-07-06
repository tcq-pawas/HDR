from django.urls import path
from . import views

app_name = 'buy'

urlpatterns = [
    path('', views.property_search, name='property_search'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('<int:pk>/inquiry/', views.send_inquiry, name='send_inquiry'),
    path('saved/', views.saved_properties, name='saved_properties'),
    path('saved/<int:pk>/add/', views.save_property, name='save_property'),
    path('saved/<int:pk>/remove/', views.remove_saved_property, name='remove_saved_property'),
]
