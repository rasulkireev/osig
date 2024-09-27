from django.urls import path

from core import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("blank-square.png", views.blank_square_image, name="blank_square_image"),
]
