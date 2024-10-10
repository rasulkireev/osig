from django.urls import path

from core import views

urlpatterns = [
    # pages
    path("", views.HomeView.as_view(), name="home"),
    path("settings", views.UserSettingsView.as_view(), name="settings"),
    path("how-to", views.HowToView.as_view(), name="how_to"),
    # blog
    path("blog", views.BlogView.as_view(), name="blog_posts"),
    path("blog/<slug:slug>", views.BlogPostView.as_view(), name="blog_post"),
    # utils
    path("resend-confirmation", views.resend_confirmation_email, name="resend_confirmation"),
    # payments
    path("pricing", views.PricingView.as_view(), name="pricing"),
    path("create-customer-portal", views.create_customer_portal_session, name="create_customer_portal_session"),
    path(
        "create-checkout-session/<int:pk>/<str:plan>/",
        views.create_checkout_session,
        name="user_upgrade_checkout_session",
    ),
    # app
    path("blank-square.png", views.blank_square_image, name="blank_square_image"),
    path("g", views.generate_image, name="generate_image"),
]
