"""Database package — SQLite-backed audit trail for quality evaluations."""
from app.db.connection import get_db_path, init_db

__all__ = ["init_db", "get_db_path"]
