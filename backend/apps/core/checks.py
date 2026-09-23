"""Reachability probes for the four datastores backing Femopedia.

Each check reports reachability as a boolean, never as an exception: this
module backs the deep health endpoint, whose entire purpose is to name which
service is unreachable. A probe that raised would take down that endpoint
along with it, so every check below catches broadly and returns False rather
than propagating.
"""

import httpx
import redis
from django.conf import settings
from django.db import connection
from neo4j import GraphDatabase


def check_postgres() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
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
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def run_all() -> dict[str, bool]:
    return {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "chroma": check_chroma(),
        "neo4j": check_neo4j(),
    }
