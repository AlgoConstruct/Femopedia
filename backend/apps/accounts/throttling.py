from rest_framework.throttling import ScopedRateThrottle


class IPScopedRateThrottle(ScopedRateThrottle):
    """A ScopedRateThrottle keyed on the client IP, never on request.user.

    The default ScopedRateThrottle keys its cache bucket on request.user.pk
    once a request is authenticated -- here that is the calling Device, and a
    fresh Device is one unauthenticated POST /api/devices/ away (finding I7
    of the accounts-core fix wave). For an endpoint that checks a credential
    (a password or a recovery code), keying on the device lets an attacker
    mint a new one before every guess and start a fresh bucket each time,
    which defeats the throttle entirely. These endpoints key on the client
    IP instead, regardless of whether the calling device is authenticated, so
    minting a new device buys an attacker nothing.
    """

    def get_cache_key(self, request, view):
        # self.scope is already set by ScopedRateThrottle.allow_request
        # before this is called.
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
