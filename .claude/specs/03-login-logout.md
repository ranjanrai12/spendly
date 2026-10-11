# Spec: Login and Logout

## Overview
Turn the existing static `GET /login` page into a working sign-in flow and replace the `/logout` stub with a real sign-out. A visitor submits email and password; the server verifies them against the hashed password in the `users` table, stores the user's id in the Flask session, and redirects to the landing page. Logging out clears the session and redirects to the landing page. This is Step 3 of the roadmap: it builds on registration (Step 2), which redirects to `/login` but deliberately creates no session, and it introduces the session mechanism that the profile page (Step 4) and all expense routes (Steps 7-9) will rely on.

## Depends on
- Step 1 — Database setup (`.claude/specs/01-database-setup.md`): `users` table (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`), `get_db()`, and the seeded demo user `demo@spendly.com` / `demo123`.
- Step 2 — Registration (`.claude/specs/02-registration.md`): users are created with `generate_password_hash` and lowercased, trimmed emails; `get_user_by_email(email)` in `database/db.py` already returns `id`, `name`, `email`, `password_hash`; successful registration redirects to `url_for('login')`.
- Existing `templates/login.html` (extends `base.html`, has an `{% if error %}` / `.auth-error` block and `email` / `password` fields).
- Existing `logout` stub route in `app.py`.
- Existing `tests/conftest.py` temporary-database client fixture (reused by the new tests).

## Routes
- `GET /login` — render the sign-in form (already implemented; unchanged) — public. A user who is already logged in is redirected to `url_for('landing')`.
- `POST /login` — validate credentials; on success store `user_id` in the session and redirect to `url_for('landing')`; on failure re-render `login.html` with HTTP 200 and an error message — public.
- `GET /register` and `POST /register` — unchanged for logged-out users; a user who is already logged in is redirected to `url_for('landing')` for both methods, before any form processing — public.
- `GET /logout` — clear the session and redirect to `url_for('landing')` — public (logging out when not logged in is harmless and also redirects).

The existing `login()` view is extended to accept `GET` and `POST`, and the existing `logout()` stub is replaced with a real implementation; no new URLs are added. `/profile` and `/expenses/*` remain stubs and are not touched.

## Database changes
No database changes. The existing `users` table already holds everything needed.

New DB helper (in `database/db.py`, not inline in the route):
- `get_user_by_id(user_id)` — parameterized `SELECT id, name, email FROM users WHERE id = ?`, returns a `sqlite3.Row` or `None`, connection closed in `finally`. It must not select `password_hash`. It lets later steps (and the navbar, if it needs the name) resolve the logged-in user from the session.

Login itself reuses the existing `get_user_by_email()`; no further helper is needed.

## Templates
- **Create:** none.
- **Modify:**
  - `templates/login.html`
    - Change the form `action` from the hardcoded `/login` to `{{ url_for('login') }}`.
    - Re-populate the `email` input with the submitted value after a failed login (never re-populate the password).
    - Keep the existing `.auth-error` block for the error message.
  - `templates/base.html`
    - In the navbar `.nav-links`, when `session.get('user_id')` is set, show a "Sign out" link to `{{ url_for('logout') }}` instead of the "Sign in" / "Get started" links; when logged out, keep the current links. All links use `url_for()`.

## Files to change
- `app.py` — import `session`, `check_password_hash`; set `app.secret_key` (read from the `SPENDLY_SECRET_KEY` environment variable, with a clearly named development fallback so the app still starts via `run.bat`); extend `login` to `GET`/`POST`; replace the `logout` stub. Route logic stays thin: read form, call DB helper, verify hash, set/clear session, redirect or render.
- `database/db.py` — add `get_user_by_id()`.
- `templates/login.html` — `url_for` form action and email re-population.
- `templates/base.html` — auth-aware navbar links.
- `CLAUDE.md` is **not** modified by this spec; updating the implemented-vs-stub table is left to the implementation step if desired.

## Files to create
- `tests/test_login_logout.py` — pytest tests covering the Definition of done, using the existing temporary-database fixtures from `tests/conftest.py` so they never touch `expense_tracker.db`.

## New dependencies
No new dependencies. Flask's built-in signed-cookie `session` and Werkzeug's `check_password_hash` are already available.

## Rules for implementation
- No SQLAlchemy or other ORMs.
- Use parameterized SQL queries only; never build SQL with f-strings or concatenation.
- Hash passwords using Werkzeug's `generate_password_hash` and verify them with `check_password_hash`. Never compare plain-text passwords, and never store or log the plain-text password.
- Use CSS variables; never hardcode hex color values.
- All page templates must extend `base.html`.
- Follow the existing database connection and transaction patterns (`get_db()`, `try/finally` with `conn.close()`).
- Never expose credentials, secrets, or sensitive user data: no password or hash in error messages, templates, session contents, or logs; the secret key must not be hardcoded as a real production secret (env var first, dev-only fallback).
- Preserve existing functionality and avoid unrelated changes; do not implement `/profile` or `/expenses/*`, and do not add route protection decorators for them (Step 4+).
- DB logic belongs in `database/db.py`, never inline in `app.py`.
- Use `url_for()` for every internal link and redirect; no hardcoded URLs.
- Do not change the port (5001).
- Login rules (server-side):
  - `email`: trimmed and lowercased before lookup (matches how registration stores it); a missing field is treated as empty, not a server error.
  - `password`: used as submitted (not trimmed); a missing field is treated as empty.
  - An unknown email, a wrong password, or empty fields all produce the **same** generic message, "Invalid email or password." — the response must not reveal whether the email exists.
  - On success store only `user_id` (integer) in the session; call `session.clear()` before setting it to avoid session fixation.
  - Do not add a "next" redirect parameter (avoids open-redirect handling in this step).
- On a failed login, re-render `login.html` with HTTP 200 and the `error` message; do not use bare string returns.
- Logout must clear the entire session (`session.clear()`), and must not require the user to be logged in.

## Definition of done
- [ ] `GET /login` returns 200 and renders a form with `email` and `password` fields posting to the URL generated by `url_for('login')` (no literal `/login` in the template's form action).
- [ ] `POST /login` with the seeded credentials `demo@spendly.com` / `demo123` returns a 302 redirect to `/` and the session contains `user_id` equal to the demo user's id.
- [ ] Login succeeds for a differently-cased / padded email such as `  Demo@Spendly.com ` with the correct password.
- [ ] `POST /login` with a correct email and wrong password returns 200, shows "Invalid email or password." in the `.auth-error` block, and the session has no `user_id`.
- [ ] `POST /login` with an unknown email returns 200 with exactly the same message as the wrong-password case.
- [ ] `POST /login` with empty fields, or with the `email` or `password` key omitted entirely, returns 200 with the same generic error (not 400/500) and sets no session.
- [ ] After a failed login, the rendered form contains the submitted email value and does not contain the submitted password.
- [ ] A user registered via `POST /register` can subsequently log in with the same email and password.
- [ ] `GET /login` while logged in returns a 302 redirect to `/`.
- [ ] While logged in, `GET /register` and `POST /register` (even with valid new-user data) return a 302 redirect to `/`, and no user row is created by the POST.
- [ ] `GET /logout` after logging in returns a 302 redirect to `/` and the session no longer contains `user_id`; `GET /logout` while logged out also returns a 302 to `/` without error.
- [ ] The navbar shows a "Sign out" link (pointing to `url_for('logout')`) and no "Sign in" / "Get started" links when logged in, and the reverse when logged out (verified by inspecting the rendered `/` response in both states).
- [ ] No response body, session value, or log output contains the submitted password or any `password_hash`; `get_user_by_id()` does not select `password_hash`.
- [ ] `database/db.py` contains `get_user_by_id()` and `app.py` contains no `sqlite3` import or SQL strings; every new query uses `?` placeholders (verified by code inspection / grep).
- [ ] `requirements.txt` is unchanged, `templates/login.html` and `templates/base.html` still extend/behave as before for logged-out users, and `/profile` and `/expenses/*` stubs are unchanged.
- [ ] `tests/test_login_logout.py` exists, uses a temporary database, and `venv\Scripts\python.exe -m pytest` passes with all tests green (including the existing registration tests).
- [ ] Manual check: starting the app with `venv\Scripts\python.exe app.py`, signing in at `http://127.0.0.1:5001/login` as `demo@spendly.com` / `demo123` lands on `/` with a "Sign out" link in the navbar, and clicking it returns to `/` with "Sign in" / "Get started" visible again.
