from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("devices/", views.create_device, name="create-device"),
]
