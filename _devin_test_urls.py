from django.urls import path, include


def dummy(request, *args, **kwargs):
    pass


public_patterns = ([
    path('', dummy, name='home'),
    path('about/', dummy, name='about'),
    path('contact/', dummy, name='contact'),
    path('agents/', dummy, name='agents'),
    path('subscription/', dummy, name='subscription_plans'),
    path('property-management/', dummy, name='property_management'),
], 'public')

buy_patterns = ([
    path('', dummy, name='property_search'),
    path('<int:pk>/', dummy, name='property_detail'),
    path('<int:pk>/save/', dummy, name='save_property'),
    path('<int:pk>/inquire/', dummy, name='send_inquiry'),
], 'buy')

sell_patterns = ([
    path('', dummy, name='sell_page'),
], 'sell')

auth_patterns = ([
    path('login/', dummy, name='login'),
    path('logout/', dummy, name='logout'),
], 'auth')

urlpatterns = [
    path('', include(public_patterns)),
    path('buy/', include(buy_patterns)),
    path('sell/', include(sell_patterns)),
    path('accounts/', include(auth_patterns)),
]
