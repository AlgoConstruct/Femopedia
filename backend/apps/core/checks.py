"""Reachability probes for the four datastores backing Femopedia.

Each check reports reachability as a boolean, never as an exception: this
module backs the deep health endpoint, whose entire purpose is to name which
service is unreachable. A probe that raised would take down that endpoint
along with it, so every check below catches broadly and returns False rather
than propagating.
"""

import httpx
import redis
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from neo4j import GraphDatabase


def check_postgres() -> bool:
    # Django runs without an explicit transaction here (no ATOMIC_REQUESTS),
    # so each cursor.execute() is its own implicit transaction and `SET
    # LOCAL` would be reset before the next statement runs. Plain `SET` is
    # session-scoped, so it is explicitly reset in the finally block to
    # avoid changing the connection's behaviour beyond this probe.
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout = '2s'")
            try:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)
            finally:
                cursor.execute("SET statement_timeout = 0")
    except Exception:
        return False


def check_redis() -> bool:
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        return bool(client.ping())
    except Exception:
        return False


def check_chroma() -> bool:
    try:
        response = httpx.get(f"{settings.CHROMA_URL}/api/v2/heartbeat", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def check_neo4j() -> bool:
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=2,
        )
        try:
            driver.verify_connectivity()
            return True
        finally:
            driver.close()
    except Exception:
        return False


def validate_identifier_crypto_settings() -> None:
    """Fail startup rather than silently degrading identifier protection.

    IDENTIFIER_PEPPER has no default (see config/settings.py), so a value
    missing entirely already raises on its own via django-environ. An empty
    string is different: it is a valid string, so it slips past that check,
    and hmac.new(b"", ...) is a perfectly valid *unkeyed* digest -- the blind
    index would still work, just be brute-forceable by anyone with the
    database, with no error anywhere to say so. `.env.example` ships both
    IDENTIFIER_PEPPER and FIELD_ENCRYPTION_KEY empty, and the README's setup
    is `cp .env.example .env`, so this is the documented path, not an edge
    case -- it must be caught here, at process startup, rather than
    discovered later from a data breach.
    """
    if not settings.IDENTIFIER_PEPPER:
        raise ImproperlyConfigured(
            "IDENTIFIER_PEPPER is empty. An empty pepper degrades the "
            "identifier blind index to an unkeyed hash anyone holding a "
            "database dump can reproduce. Generate one with:\n"
            "    python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )

    try:
        Fernet(settings.FIELD_ENCRYPTION_KEY.encode("utf-8"))
    except Exception as exc:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY is not a valid Fernet key. Generate one "
            "with:\n"
            "    python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"'
        ) from exc


def run_all() -> dict[str, bool]:
    return {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "chroma": check_chroma(),
        "neo4j": check_neo4j(),
    }
