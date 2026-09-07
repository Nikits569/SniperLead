from django.urls import path
from . views import *

urlpatterns = [
    path('create-checkout-session/',CreateCheckoutSessionView.as_view(),name='create-checkout-session'),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('dashboard/', dashboard_view, name='dashboard'),
]
