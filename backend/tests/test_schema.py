import io

import pytest
import yaml
from django.core.management import call_command
from django.test import Client, override_settings

SCHEMA_URLS = ("/api/schema/", "/api/docs/", "/api/redoc/")


@pytest.fixture
def schema():
    """The schema as the generator produces it right now."""
    buffer = io.StringIO()
    call_command("spectacular", "--validate", "--fail-on-warn", stdout=buffer)
    return yaml.safe_load(buffer.getvalue())


# --- access control -------------------------------------------------------
# Django forces DEBUG=False during tests, so the default case here is the
# deployed one.


@pytest.mark.parametrize("url", SCHEMA_URLS)
@pytest.mark.django_db
def test_schema_is_not_public_without_debug_or_token(url):
    with override_settings(DOCS_TOKEN=""):
        assert Client().get(url).status_code == 403


@pytest.mark.parametrize("url", SCHEMA_URLS)
@pytest.mark.django_db
def test_schema_is_served_to_a_correct_docs_token(url):
    with override_settings(DOCS_TOKEN="a-real-docs-token"):
        response = Client().get(url, headers={"x-docs-token": "a-real-docs-token"})
    assert response.status_code == 200


@pytest.mark.django_db
def test_schema_rejects_a_wrong_docs_token():
    with override_settings(DOCS_TOKEN="a-real-docs-token"):
        response = Client().get("/api/schema/", headers={"x-docs-token": "wrong"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_an_unset_docs_token_denies_rather_than_matching_an_empty_header():
    with override_settings(DOCS_TOKEN=""):
        response = Client().get("/api/schema/", headers={"x-docs-token": ""})
    assert response.status_code == 403


@pytest.mark.django_db
def test_schema_is_served_under_debug():
    with override_settings(DEBUG=True, DOCS_TOKEN=""):
        assert Client().get("/api/schema/").status_code == 200


# --- schema content -------------------------------------------------------


def test_device_token_security_scheme_is_documented(schema):
    scheme = schema["components"]["securitySchemes"]["DeviceToken"]
    assert scheme["type"] == "apiKey"
    assert scheme["in"] == "header"
    assert scheme["name"] == "X-Device-Token"


def test_bootstrap_endpoints_are_documented_as_requiring_no_credential(schema):
    # A device cannot hold a token before POST /api/devices/ gives it one, and
    # the probes must answer without a credential, so none of these may carry a
    # DeviceToken requirement. An absent "security" key means no requirement,
    # since the schema declares no global security.
    assert "security" not in schema
    for path, method in (
        ("/api/devices/", "post"),
        ("/api/health/", "get"),
        ("/api/health/deep/", "get"),
    ):
        requirements = schema["paths"][path][method].get("security", [])
        assert all("DeviceToken" not in r for r in requirements), path


def test_whoami_is_documented_as_requiring_the_device_token(schema):
    security = schema["paths"]["/api/whoami/"]["get"]["security"]
    assert {"DeviceToken": []} in security


def test_schema_does_not_document_its_own_routes(schema):
    for url in SCHEMA_URLS:
        assert url not in schema["paths"]


def test_committed_schema_matches_the_generated_one(schema, settings):
    """schema.yml is consumed by the frontend's type generation, so a drifted
    copy silently produces wrong client types. CI runs this too."""
    committed = yaml.safe_load((settings.BASE_DIR / "schema.yml").read_text())
    assert committed == schema, "schema.yml is stale — regenerate it (see README)"
