import base64
import inspect
import os
import subprocess
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

import database.db as db

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO = {"email": "demo@spendly.com", "password": "demo123"}
GENERIC_ERROR = "Invalid email or password."
OTHER = {"name": "Other User", "email": "other@example.com", "password": "otherpass99"}


def demo_id():
    return db.get_user_by_email(DEMO["email"])["id"]


def session_user_id(client):
    with client.session_transaction() as sess:
        return sess.get("user_id")


def login(client, **overrides):
    return client.post("/login", data={**DEMO, **overrides})


def make_other_user():
    return db.create_user(
        OTHER["name"], OTHER["email"], generate_password_hash(OTHER["password"])
    )


def user_count():
    conn = db.get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


# ---------------------------------------------------------------- login

def test_login_form_renders_with_url_for_action(client):
    response = client.get("/login")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'action="/login"' in html
    assert 'name="email"' in html and 'name="password"' in html


def test_login_success_sets_int_user_id_and_redirects(client):
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    user_id = session_user_id(client)
    assert isinstance(user_id, int)
    assert user_id == demo_id()


def test_login_accepts_padded_mixed_case_email(client):
    response = login(client, email="  Demo@Spendly.com ")
    assert response.status_code == 302
    assert session_user_id(client) == demo_id()


def test_wrong_password_and_unknown_email_give_identical_error(client):
    wrong_pw = login(client, password="not-the-password")
    unknown = login(client, email="nobody@example.com")
    for response in (wrong_pw, unknown):
        html = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "auth-error" in html
        assert GENERIC_ERROR in html
        assert session_user_id(client) is None


def test_empty_and_missing_fields_give_generic_error(client):
    cases = [
        {"email": "", "password": ""},
        {"email": DEMO["email"]},
        {"password": DEMO["password"]},
        {},
    ]
    for data in cases:
        response = client.post("/login", data=data)
        assert response.status_code == 200
        assert GENERIC_ERROR in response.get_data(as_text=True)
        assert session_user_id(client) is None


def test_failed_login_echoes_email_not_password(client):
    response = login(client, password="secret-attempt-123")
    html = response.get_data(as_text=True)
    assert f'value="{DEMO["email"]}"' in html
    assert "secret-attempt-123" not in html


def test_registered_user_can_log_in(client):
    client.post(
        "/register",
        data={
            "name": "New Person",
            "email": "new@example.com",
            "password": "longenough1",
            "confirm_password": "longenough1",
        },
    )
    response = client.post(
        "/login", data={"email": "new@example.com", "password": "longenough1"}
    )
    assert response.status_code == 302
    assert session_user_id(client) == db.get_user_by_email("new@example.com")["id"]


def test_login_get_while_logged_in_redirects(client):
    login(client)
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


# ---------------------------------------------------------------- register guard

def test_register_get_while_logged_in_redirects_home(client):
    login(client)
    response = client.get("/register")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_register_post_while_logged_in_redirects_and_creates_no_user(client):
    login(client)
    before = user_count()
    response = client.post(
        "/register",
        data={
            "name": "Sneaky",
            "email": "sneaky@example.com",
            "password": "longenough1",
            "confirm_password": "longenough1",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert user_count() == before


def test_register_get_logged_out_still_renders(client):
    assert client.get("/register").status_code == 200


# ---------------------------------------------------------------- logout

def test_logout_clears_session(client):
    login(client)
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert session_user_id(client) is None


def test_logout_when_logged_out_still_redirects(client):
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


# ---------------------------------------------------------------- navbar

def test_navbar_logged_out(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/login"' in html
    assert 'href="/register"' in html
    assert 'href="/logout"' not in html
    assert "Sign out" not in html


def test_navbar_logged_in(client):
    login(client)
    html = client.get("/").get_data(as_text=True)
    assert 'href="/logout"' in html
    assert "Sign out" in html
    assert 'href="/login"' not in html
    assert "Get started" not in html


# ---------------------------------------------------------------- session isolation

def test_logged_in_wrong_credentials_post_keeps_identity(client):
    login(client)
    response = login(client, password="wrong-password")
    assert response.status_code == 302
    assert session_user_id(client) == demo_id()


def test_logged_in_post_with_other_valid_user_does_not_switch_identity(client):
    make_other_user()
    login(client)
    response = client.post(
        "/login", data={"email": OTHER["email"], "password": OTHER["password"]}
    )
    assert response.status_code == 302
    assert session_user_id(client) == demo_id()


def test_stale_non_auth_session_and_failed_login_gives_no_user_id(client):
    with client.session_transaction() as sess:
        sess["stale"] = "value"
    response = login(client, password="wrong-password")
    assert response.status_code == 200
    assert GENERIC_ERROR in response.get_data(as_text=True)
    assert session_user_id(client) is None


# ---------------------------------------------------------------- get_user_by_id

def test_get_user_by_id_existing_returns_safe_fields(client):
    user = db.get_user_by_id(demo_id())
    assert set(user.keys()) == {"id", "name", "email", "created_at"}
    assert user["name"] == "Demo User"
    assert user["email"] == DEMO["email"]


def test_get_user_by_id_unknown_returns_none(client):
    assert db.get_user_by_id(99999) is None


def test_get_user_by_id_does_not_expose_hash(client):
    stored_hash = db.get_user_by_email(DEMO["email"])["password_hash"]
    user = db.get_user_by_id(demo_id())
    assert "password_hash" not in user.keys()
    assert stored_hash not in [str(value) for value in tuple(user)]


def test_get_user_by_id_injection_string_returns_none(client):
    assert db.get_user_by_id("1 OR 1=1") is None


def test_get_user_by_id_source_is_parameterized_and_omits_hash():
    source = inspect.getsource(db.get_user_by_id)
    assert "?" in source
    assert "password_hash" not in source


# ---------------------------------------------------------------- exposure

def _decode_cookie_payload(set_cookie_header):
    value = set_cookie_header.split("session=", 1)[1].split(";", 1)[0]
    payload = value.lstrip(".").split(".", 1)[0]
    payload += "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload.encode()).decode(errors="replace")


def test_no_password_or_hash_in_responses_or_session(client):
    stored_hash = db.get_user_by_email(DEMO["email"])["password_hash"]
    password = DEMO["password"]

    failed_html = login(client, password="wrong-attempt-xyz").get_data(as_text=True)
    assert "wrong-attempt-xyz" not in failed_html
    assert stored_hash not in failed_html

    success = login(client)
    followed = client.get("/")
    for body in (success.get_data(as_text=True), followed.get_data(as_text=True)):
        assert password not in body
        assert stored_hash not in body

    with client.session_transaction() as sess:
        assert set(sess.keys()) == {"user_id"}
        assert password not in str(dict(sess))
        assert stored_hash not in str(dict(sess))

    cookie = success.headers.get("Set-Cookie", "")
    assert cookie
    assert password not in cookie and stored_hash not in cookie
    decoded = _decode_cookie_payload(cookie)
    assert password not in decoded and stored_hash not in decoded


# ---------------------------------------------------------------- production secret

def _import_app_in_subprocess(env_overrides):
    return subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=REPO_ROOT,
        env={**os.environ, **env_overrides},
        capture_output=True,
        text=True,
    )


def test_production_without_secret_fails_fast():
    for key in ("", "   "):
        result = _import_app_in_subprocess(
            {"SPENDLY_ENV": "production", "SPENDLY_SECRET_KEY": key}
        )
        assert result.returncode != 0
        assert "RuntimeError" in result.stderr
        assert "SPENDLY_SECRET_KEY" in result.stderr


def test_production_failure_does_not_print_dev_fallback(client):
    import app as app_module

    result = _import_app_in_subprocess(
        {"SPENDLY_ENV": "production", "SPENDLY_SECRET_KEY": ""}
    )
    assert app_module._DEV_ONLY_SECRET_KEY not in result.stdout + result.stderr
