from django.urls import path

from core import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("settings", views.UserSettingsView.as_view(), name="settings"),
    path("resend-confirmation/", views.resend_confirmation_email, name="resend_confirmation"),
    path("blank-square.png", views.blank_square_image, name="blank_square_image"),
    path("g", views.generate_image, name="generate_image"),
]
