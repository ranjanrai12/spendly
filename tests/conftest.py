import pytest

import database.db as db


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Point the DB at a temp file before app is imported, so the import-time
    # init_db()/seed_db() in app.py never touch expense_tracker.db.
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()

    import app as app_module

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client
