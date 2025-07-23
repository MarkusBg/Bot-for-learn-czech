import pytest
from database.db import Database
import os

def test_create_tables(tmp_path):
    db_path = tmp_path / 'test.db'
    db = Database(str(db_path))
    # Проверяем, что таблицы созданы
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert 'users' in tables
    assert 'words' in tables
    assert 'feedback' in tables
    assert 'user_states' in tables
    db.close() 