from unittest import mock

import pytest
from django.test import Client

from apps.core import checks


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
def test_deep_health_reports_503_when_any_service_is_down():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": False, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    assert response.status_code == 503
    assert response.json()["services"]["redis"] is False


@pytest.mark.django_db
def test_deep_health_reports_200_when_everything_is_up():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": True, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.django_db
def test_all_services_are_reachable_under_docker_compose():
    assert checks.run_all() == {
        "postgres": True,
        "redis": True,
        "chroma": True,
        "neo4j": True,
    }
