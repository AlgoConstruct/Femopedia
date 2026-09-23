import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-real-secret")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///test-db.sqlite3")
