"""Database package — SQLite-backed audit trail for quality evaluations."""
from app.db.connection import init_db, get_db_path

__all__ = ["init_db", "get_db_path"]
