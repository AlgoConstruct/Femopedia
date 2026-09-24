from django.urls import path

from apps.accounts import auth_views, views

urlpatterns = [
    path("devices/", views.create_device, name="create-device"),
    path("auth/signup/", auth_views.signup, name="auth-signup"),
]
