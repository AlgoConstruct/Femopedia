from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, override_settings

from apps.core import checks

# --- I5: an empty IDENTIFIER_PEPPER or an invalid FIELD_ENCRYPTION_KEY must
# fail startup, not silently degrade -----------------------------------------
#
# IDENTIFIER_PEPPER has no default in config/settings.py, so a value missing
# entirely already raises via django-environ before this function is ever
# reached. An *empty string* is different: it's a valid string, so it slips
# past that check, and hmac.new(b"", ...) is a valid unkeyed digest -- the
# blind index would still work, just be brute-forceable by anyone holding a
# database dump, with nothing anywhere to say so. .env.example ships both
# keys empty and the README's setup is `cp .env.example .env`, so this is
# the documented path, not an edge case.


def test_validate_identifier_crypto_settings_rejects_an_empty_pepper():
    with (
        override_settings(IDENTIFIER_PEPPER=""),
        pytest.raises(ImproperlyConfigured, match="IDENTIFIER_PEPPER"),
    ):
        checks.validate_identifier_crypto_settings()


def test_validate_identifier_crypto_settings_rejects_an_invalid_fernet_key():
    with (
        override_settings(FIELD_ENCRYPTION_KEY="not-a-valid-fernet-key"),
        pytest.raises(ImproperlyConfigured, match="FIELD_ENCRYPTION_KEY"),
    ):
        checks.validate_identifier_crypto_settings()


def test_validate_identifier_crypto_settings_passes_for_valid_settings():
    """The test environment's own values (pyproject.toml's [tool.pytest.
    ini_options].env block) must themselves pass, since AccountsConfig.ready()
    now calls this at every process start, including under pytest."""
    checks.validate_identifier_crypto_settings()


def test_each_check_returns_false_when_the_backend_raises():
    with mock.patch("apps.core.checks.connection.cursor", side_effect=OSError("down")):
        assert checks.check_postgres() is False

    with mock.patch("apps.core.checks.redis.Redis.from_url", side_effect=OSError("down")):
        assert checks.check_redis() is False

    with mock.patch("apps.core.checks.httpx.get", side_effect=OSError("down")):
        assert checks.check_chroma() is False

    with mock.patch("apps.core.checks.GraphDatabase.driver", side_effect=OSError("down")):
        assert checks.check_neo4j() is False


def test_check_neo4j_closes_the_driver_when_verify_connectivity_raises():
    mock_driver = mock.MagicMock()
    mock_driver.verify_connectivity.side_effect = OSError("down")
    with mock.patch("apps.core.checks.GraphDatabase.driver", return_value=mock_driver):
        assert checks.check_neo4j() is False
    mock_driver.close.assert_called_once()


@pytest.mark.django_db
def test_check_postgres_is_true_against_the_test_database():
    assert checks.check_postgres() is True


@pytest.mark.django_db
def test_deep_health_reports_503_when_a_required_service_is_down():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": False, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    body = response.json()
    assert response.status_code == 503
    assert body["status"] == "down"
    assert body["services"]["redis"] is False


@pytest.mark.django_db
def test_deep_health_reports_200_when_everything_is_up():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": True, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"


@pytest.mark.django_db
def test_deep_health_reports_200_and_degraded_when_only_a_derived_service_is_down():
    """Chroma and Neo4j hold derived, rebuildable data (plan's global
    constraints), so an anticipated rebuild of either must not read as an
    outage of the whole API — it should look like a normal, healthy 200
    with a "degraded" status alongside the per-service breakdown.
    """
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": True, "chroma": False, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "degraded"
    assert body["services"]["chroma"] is False


@pytest.mark.django_db
def test_deep_health_reports_503_when_a_required_service_is_down_even_if_derived_services_are_up():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": False, "redis": True, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    body = response.json()
    assert response.status_code == 503
    assert body["status"] == "down"


@pytest.mark.integration
@pytest.mark.django_db
def test_all_services_are_reachable_under_docker_compose():
    assert checks.run_all() == {
        "postgres": True,
        "redis": True,
        "chroma": True,
        "neo4j": True,
    }
