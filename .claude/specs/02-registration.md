# Spec: Registration

## Overview
Turn the existing static `GET /register` page into a working sign-up flow. A visitor submits name, email and password; the server validates the input, stores a new user with a hashed password in the `users` table, and redirects to the login page. This is Step 2 of the roadmap: it builds directly on the data layer from Step 1 and must exist before login/logout (Step 3) and the profile page (Step 4) can be implemented. Registration does not create a session; logging in remains Step 3.

## Depends on
- Step 1 — Database setup (`.claude/specs/01-database-setup.md`): `users` table (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`), `get_db()` (sets `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`), and `init_db()` / `seed_db()` called at startup in `app.py`.
- Existing `templates/register.html` (extends `base.html`, already has an `{% if error %}` block and fields `name`, `email`, `password`).
- Existing `login` route, used as the redirect target after success.

## Routes
- `GET /register` — render the registration form (already implemented; unchanged) — public.
- `POST /register` — validate the submitted form, create the user, redirect to `url_for('login')` on success, or re-render `register.html` with an error message on failure — public.

The existing `register()` view in `app.py` is extended to accept `GET` and `POST`; no new URL is added.

## Database changes
No database changes. The existing `users` table already provides everything needed (`name TEXT NOT NULL`, `email TEXT NOT NULL UNIQUE`, `password_hash TEXT NOT NULL`, `created_at` default). Duplicate emails are rejected by the existing `UNIQUE` constraint on `users.email`.

New DB helper functions (in `database/db.py`, not inline in the route):
- A function to look up a user by email (parameterized `SELECT`), used to detect an already-registered email.
- A function to insert a new user from name, email and an already-hashed password (parameterized `INSERT`, committed, connection closed in `finally`, rollback on error), returning the new user's id. It must surface a duplicate-email `sqlite3.IntegrityError` so the route can handle a race between the lookup and the insert.

## Templates
- **Create:** none.
- **Modify:** `templates/register.html`
  - Change the form `action` from the hardcoded `/register` to `{{ url_for('register') }}`.
  - Re-populate the `name` and `email` inputs with the submitted values after a validation error (never re-populate the password).
  - Keep the existing `.auth-error` block for displaying the error message.

## Files to change
- `app.py` — import `request`, `redirect`, `url_for` (and `generate_password_hash`); let the `register` route accept `GET` and `POST`; validate input; call the DB helpers; redirect or re-render with an error. Route logic stays thin: validate, call helpers, render/redirect.
- `database/db.py` — add the user lookup and user creation helpers described above.
- `templates/register.html` — `url_for` form action and value re-population, as above.

## Files to create
- `tests/test_registration.py` — pytest tests covering the Definition of done (there is currently no `tests/` directory; pytest and pytest-flask are already in `requirements.txt`). Tests must use a temporary database (e.g. by pointing `DB_PATH` at a temp file) so they never touch `expense_tracker.db`.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or other ORMs.
- Use parameterized SQL queries only; never build SQL with f-strings or concatenation.
- Hash passwords using Werkzeug's `generate_password_hash` and verify them with `check_password_hash`. Never store or log the plain-text password.
- Use CSS variables; never hardcode hex color values.
- All page templates must extend `base.html`.
- Follow the existing database connection and transaction patterns (`get_db()`, `try/finally` with `conn.close()`, `commit()` after writes, `rollback()` on error).
- Never expose credentials, secrets, or sensitive user data (no password or hash in error messages, templates, or logs).
- Preserve existing functionality and avoid unrelated changes; do not implement the `/logout`, `/profile`, or `/expenses/*` stubs, and do not implement login (Step 3).
- DB logic belongs in `database/db.py`, never inline in `app.py`.
- Use `url_for()` for every internal link and redirect; no hardcoded URLs.
- Do not change the port (5001).
- Validation rules (server-side, regardless of HTML `required`):
  - `name`: trimmed, non-empty.
  - `email`: trimmed, lowercased before lookup and storage, non-empty, and containing `@` with non-empty parts around it.
  - `password`: at least 8 characters (matches the existing form placeholder "Min. 8 characters").
  - A missing form field is treated as empty, not as a server error.
- On a validation or duplicate-email error, re-render `register.html` with HTTP 200 and a specific `error` message; do not use bare string returns.
- No session or `secret_key` is introduced in this step; successful registration redirects to the login page only.

## Definition of done
- [ ] `GET /register` returns 200 and renders a form with `name`, `email` and `password` fields posting to the URL generated by `url_for('register')` (no literal `/register` in the template's form action).
- [ ] `POST /register` with a valid name, new email and an 8+ character password creates exactly one new row in `users` and responds with a 302 redirect to `/login`.
- [ ] The stored `password_hash` for the new user differs from the submitted password and `check_password_hash(stored_hash, submitted_password)` returns `True`.
- [ ] Submitting an email that already exists (including the seeded `demo@spendly.com` and a differently-cased variant such as `Demo@Spendly.com`) returns 200, shows an error message in the `.auth-error` block, and leaves the `users` row count unchanged.
- [ ] Submitting an empty name, empty/invalid email (e.g. `foo`), or a password shorter than 8 characters returns 200 with an error message and creates no user.
- [ ] After a failed submission, the rendered form contains the submitted name and email values and does not contain the submitted password.
- [ ] Emails are stored trimmed and lowercased (verified by registering `  New@Example.com ` and reading the row back).
- [ ] A submission with a missing field (e.g. no `password` key) returns 200 with an error, not a 400/500.
- [ ] `database/db.py` contains the new helpers and `app.py` contains no `sqlite3` or SQL strings; every new query uses `?` placeholders (verified by code inspection / grep).
- [ ] `requirements.txt` is unchanged and `templates/register.html` still extends `base.html`.
- [ ] `tests/test_registration.py` exists, uses a temporary database, and `venv\Scripts\python.exe -m pytest` passes with all tests green.
- [ ] Manual check: starting the app with `venv\Scripts\python.exe app.py`, registering through the browser at `http://127.0.0.1:5001/register` lands on `/login`, and the new user appears in `expense_tracker.db`.
