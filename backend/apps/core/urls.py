from django.urls import path

from apps.core import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("health/deep/", views.health_deep, name="health-deep"),
    path("whoami/", views.whoami, name="whoami"),
]
