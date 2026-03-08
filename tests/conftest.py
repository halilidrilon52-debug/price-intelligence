"""Pytest conftest: set SECRET_KEY so app import works when .env is missing (e.g. CI)."""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci")
