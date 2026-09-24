from rest_framework.permissions import BasePermission


class RequiresAccount(BasePermission):
    """Deny an anonymous device the same way, everywhere.

    Many endpoints only make sense for a device bound to an account
    (account summary, device list/revoke, password change, export, delete).
    Each used to re-implement "if request.auth.account is None: return 403"
    with its own copy of the response body. This is the one place that
    check lives now; the body DRF renders for a failed permission
    (`{"detail": self.message}`, status 403) matches what those call sites
    returned by hand.
    """

    message = "This device is not signed in."

    def has_permission(self, request, view) -> bool:
        return request.auth is not None and request.auth.account is not None
