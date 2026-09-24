import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_is_postgres():
    assert connection.vendor == "postgresql"


@pytest.mark.django_db
def test_pgvector_extension_is_available():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        assert cursor.fetchone() is not None
