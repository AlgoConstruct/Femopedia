from django.urls import path

from apps.accounts import auth_views, session_views, views

urlpatterns = [
    path("devices/", views.create_device, name="create-device"),
    path("auth/signup/", auth_views.signup, name="auth-signup"),
    path("auth/verify-email/", auth_views.verify_email, name="auth-verify-email"),
    path("auth/recover/", auth_views.recover, name="auth-recover"),
    path("auth/login/", session_views.login, name="auth-login"),
    path("auth/logout/", session_views.logout, name="auth-logout"),
    path("auth/password-reset/", auth_views.password_reset, name="auth-password-reset"),
    path(
        "auth/password-reset/confirm/",
        auth_views.password_reset_confirm,
        name="auth-password-reset-confirm",
    ),
    path("account/password/", auth_views.password_change, name="account-password"),
]
