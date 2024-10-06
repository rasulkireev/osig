from django.urls import path

from core import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("settings", views.UserSettingsView.as_view(), name="settings"),
    path("pricing", views.PricingView.as_view(), name="pricing"),
    path("resend-confirmation", views.resend_confirmation_email, name="resend_confirmation"),
    path("create-customer-portal", views.create_customer_portal_session, name="create_customer_portal_session"),
    path("blank-square.png", views.blank_square_image, name="blank_square_image"),
    path("g", views.generate_image, name="generate_image"),
    path(
        "create-checkout-session/<int:pk>/<str:plan>/",
        views.create_checkout_session,
        name="user_upgrade_checkout_session",
    ),
]
