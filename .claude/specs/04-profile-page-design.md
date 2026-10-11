# Spec: Profile Page Design

## Overview
Replace the `/profile` stub (which currently returns the raw string "Profile page — coming in Step 4") with a designed, login-protected profile page. The page shows the signed-in user's account details (name, email, member-since date), a spending summary (total spent, number of expenses, this month's total), a per-category breakdown, and a list of recent expenses, all read from the existing `users` and `expenses` tables. This is Step 4 of the roadmap: it builds on login/logout (Step 3), which introduced `session["user_id"]` and `get_user_by_id()`, and it is the first page that requires an authenticated user, so it also establishes the logged-out redirect pattern for later steps (7-9). Visual design must follow the project's UI skill (`.claude/skills/frontend-design/SKILL.md`, name `spendly-ui-designer`): a clean, card-based, fintech-style layout with restrained shadows, an 8px spacing grid, and Lucide icons. Because Spendly already has an established palette and fonts in `static/css/style.css`, those existing tokens take precedence over the skill's default palette (the skill says to override its defaults to match existing styles).

## Depends on
- Step 1 — Database setup (`.claude/specs/01-database-setup.md`): `users` (`id`, `name`, `email`, `password_hash`, `created_at`) and `expenses` (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) tables, `get_db()` with `PRAGMA foreign_keys = ON`, and seeded demo data (`demo@spendly.com` / `demo123` with 8 expenses in the current month).
- Step 2 — Registration (`.claude/specs/02-registration.md`): newly registered users have zero expenses, so the empty state must render.
- Step 3 — Login and logout (`.claude/specs/03-login-logout.md`): `session["user_id"]` (integer), `get_user_by_id(user_id)` in `database/db.py`, auth-aware navbar in `templates/base.html`, and the `tests/conftest.py` temporary-database client fixture.
- Existing `profile` stub route in `app.py`.
- Existing design tokens (CSS variables) and navbar/footer styles in `static/css/style.css` (`--paper`, `--paper-card`, `--accent`, `--border`, `--ink*`, `--radius-*`, `--font-display`, `--font-body`).
- `.claude/skills/frontend-design/SKILL.md` — design language the page must follow.

## Routes
- `GET /profile` — render the profile page for the user in the session — logged-in. If there is no `user_id` in the session, redirect to `url_for('login')` (302). If the session `user_id` no longer matches a user row, clear the session and redirect to `url_for('login')`.

The existing `profile()` stub is replaced; no new URLs are added. `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` remain stubs and are not touched.

## Database changes
No database changes (no new tables, columns, constraints, or indexes). Amounts are `REAL`, dates are ISO `YYYY-MM-DD` text, so month filtering can use a parameterized `date LIKE ?` / `substr(date, 1, 7) = ?` comparison.

New read-only helpers in `database/db.py` (not inline in the route), each following the existing `get_db()` + `try/finally conn.close()` pattern, using `?` placeholders, and always scoped by `user_id`:
- `get_user_by_id(user_id)` — already exists; reused for name/email. Needs `created_at` for "member since": extend its `SELECT` to `id, name, email, created_at` (still must not select `password_hash`). Existing callers only read `id`/`name`/`email`, so this is backward compatible.
- `get_expense_summary(user_id, month)` — returns total amount, expense count, and total for `month` (`"YYYY-MM"` string passed in by the route); zero values (not `None`) when the user has no expenses.
- `get_category_totals(user_id)` — returns `(category, total, count)` rows grouped by category, ordered by total descending.
- `get_recent_expenses(user_id, limit=10)` — returns `id, amount, category, date, description` ordered by `date DESC, id DESC`, limited by a bound `?` parameter.

## Templates
- **Create:**
  - `templates/profile.html` — extends `base.html`; sections: profile header (avatar initial, name, email, member since), summary stat cards, category breakdown, recent expenses list, and an empty state when the user has no expenses.
- **Modify:**
  - `templates/base.html` — when logged in, add a "Profile" link (`{{ url_for('profile') }}`) to `.nav-links` next to "Sign out". Logged-out navbar unchanged. Also load Lucide once via the skill's CDN script tag and call `lucide.createIcons()` after DOM ready (see Rules; this is a CDN script, not an npm/pip package).
  - Page-specific CSS is loaded from `profile.html` via `{% block head %}` (see Files to create); no inline `<style>` tags.

## Files to change
- `app.py` — import `abort` if needed and the new DB helpers; replace the `profile` stub: read `session.get("user_id")`, redirect to `url_for('login')` if missing, fetch user + summary + categories + recent expenses via DB helpers, `render_template("profile.html", ...)`. Route stays thin (fetch, render, done). Use `abort()` rather than a bare string for any error response.
- `database/db.py` — extend `get_user_by_id()` to include `created_at`; add `get_expense_summary()`, `get_category_totals()`, `get_recent_expenses()`.
- `templates/base.html` — logged-in "Profile" nav link; Lucide CDN script and `lucide.createIcons()` call.
- `static/css/style.css` — only if needed: add new variables to `:root` (e.g. a `--shadow-card` token and a spacing scale `--space-1`..`--space-6` on the 8px grid) so `profile.css` never needs raw color or shadow literals.
- `static/js/main.js` — only the `lucide.createIcons()` initialization, if not placed inline in `base.html`.
- `CLAUDE.md` is **not** modified by this spec; flipping `/profile` to "Implemented" in its route table is left to the implementation step if desired.

## Files to create
- `templates/profile.html` — the profile page template.
- `static/css/profile.css` — profile-page-only styles (stat cards, category bars, recent-expense list, responsive layout), using only existing CSS variables from `style.css`.
- `tests/test_profile.py` — pytest tests covering the Definition of done, using the temporary-database fixtures from `tests/conftest.py` so they never touch `expense_tracker.db`.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or other ORMs.
- Use parameterized SQL queries only; never build SQL with f-strings or concatenation (this includes the `LIMIT` and the month filter).
- Hash passwords using Werkzeug's `generate_password_hash` and verify them with `check_password_hash` (no password handling is expected on this page; do not add any).
- Use CSS variables; never hardcode hex color values. Add any new colors as variables in `:root` of `style.css` only if the existing tokens are insufficient; `profile.css` itself must contain no hex/rgb literals.
- All page templates must extend `base.html`.
- Follow the existing database connection and transaction patterns (`get_db()`, `try/finally` with `conn.close()`).
- Never expose credentials, secrets, or sensitive user data: no `password_hash` in queries, templates, or session; the page shows only the logged-in user's own data.
- Preserve existing functionality and avoid unrelated changes; do not implement `/expenses/*` stubs or add expense create/edit/delete UI (Steps 7-9). Do not add a filter/date-range UI (out of scope for this step).
- DB logic belongs in `database/db.py`; `app.py` contains no `sqlite3` import or SQL strings.
- Use `url_for()` for every internal link and redirect; no hardcoded URLs. Static assets via `url_for('static', filename=...)`.
- Every expense query must be filtered by the session user's `user_id` so one user can never see another's expenses.
- Jinja2 autoescaping must stay on; expense descriptions and categories are user-entered, never use `|safe`.
- Design language (from `.claude/skills/frontend-design/SKILL.md`):
  - Reuse existing tokens/classes from `style.css` first; the skill's default hex palette applies only where Spendly has no equivalent. One primary accent (`--accent`); `--danger` / `--accent-2` only for semantic meaning; everything else neutral. Expense amounts may use `--danger`-style semantics only if it stays consistent across the page.
  - Card-based composition: group related info in white `--paper-card` surfaces with a soft `--border` and/or a subtle shadow (ceiling: `0 1px 2px` + `0 1px 3px` at very low alpha, defined once as a `:root` variable). No glows, gradients, or heavy drop shadows.
  - 8px spacing grid: padding, gap, and margin are multiples of 4px/8px (use spacing variables); no arbitrary values like 13px or 27px. Use the same card padding everywhere.
  - Radius: 8px for small elements, 12px for cards, fully rounded for pills/badges (map to existing `--radius-sm` / `--radius-md` where they match).
  - Typography: existing `--font-display` / `--font-body`; type scale 12 / 14 / 16 / 20 / 24 / 32px; weights 400 body, 500 medium, 600 headings. All amounts use `font-variant-numeric: tabular-nums`.
  - Layout: left-aligned content with clear hierarchy and generous whitespace; centered layout only for the empty state. Tables/lists: row hover state, numeric columns right-aligned.
  - Icons: Lucide via `<i data-lucide="...">`, loaded once in `base.html` (the CDN script pinned to a specific version, not `@latest`) and initialized with `lucide.createIcons()`. Density: one icon per section heading and per stat card, none sprinkled elsewhere; sizes 16px inline, 20px buttons, 24px section headers. Suggested icons: `wallet`, `calendar`, `tag`, `pie-chart`, `credit-card`, `user`. The page must remain fully readable if the CDN fails to load (icons are decorative, with text labels always present).
  - Styles are scoped with a `.profile-` class prefix so they do not leak into other pages.
  - Responsive: cards stack vertically at narrow widths and the recent-expenses table scrolls horizontally inside its own wrapper below ~768px (no page-level horizontal scroll).
- Display currency as rupees (`₹`) with two decimals, matching the "Track every rupee" branding; a `NULL` description renders as an em dash or is omitted, not the text "None".
- Vanilla JS only; the page should work without any JavaScript (no new JS required).
- The design must be responsive (readable at 360px width and at the 1200px `--max-width`), use the existing `--font-display` / `--font-body` fonts, and follow the frontend-design skill's guidance.
- Do not change the port (5001).

## Definition of done
- [ ] `GET /profile` while logged out returns a 302 redirect to `/login` (generated via `url_for('login')`) and does not render user data.
- [ ] `GET /profile` while logged in as the seeded demo user returns 200 and the body contains "Demo User" and "demo@spendly.com".
- [ ] The page shows a "member since" value derived from the user's `created_at`.
- [ ] For the demo user, the total spent shown equals the sum of the 8 seeded amounts (₹279.84) and the expense count shows 8; the "this month" total equals the sum of seeded expenses dated in the current month (verified in a test that inserts expenses with known dates, including one outside the current month that must be excluded from the monthly total).
- [ ] The category breakdown lists each category with its total and is ordered by total descending (e.g. for the demo user "Bills" appears before "Food").
- [ ] The recent-expenses list shows at most 10 rows ordered newest first; a test with 12 expenses asserts exactly 10 rows and the oldest two are absent.
- [ ] An expense with a `NULL` description renders without the literal text "None".
- [ ] A newly registered user with zero expenses gets 200 with zeros (`₹0.00`, count 0) and a visible empty-state message, with no server error.
- [ ] A second user's expenses never appear on the first user's profile (test creates two users with distinct expenses and asserts isolation).
- [ ] If the session holds a `user_id` that does not exist in `users`, `GET /profile` returns a 302 to `/login` and the session no longer contains `user_id`.
- [ ] Expense descriptions containing HTML (e.g. `<script>alert(1)</script>`) appear escaped in the response body.
- [ ] The rendered page never contains `password_hash` or any hash string; `get_user_by_id()` still does not select `password_hash` (code inspection / grep).
- [ ] When logged in, the navbar shows a "Profile" link pointing to `url_for('profile')` and "Sign out"; when logged out it shows neither "Profile" nor "Sign out" (verified by inspecting rendered `/` in both states).
- [ ] `templates/profile.html` extends `base.html`, includes `static/css/profile.css` via `url_for`, and contains no inline `<style>` tag and no hardcoded internal URLs (grep).
- [ ] `static/css/profile.css` contains no hex color literals and no `rgb(`/`rgba(` literals (grep for `#[0-9a-fA-F]{3,8}` and `rgba?\(`); shadows and colors come from `:root` variables.
- [ ] All `profile.css` selectors are prefixed `.profile-` (grep), and padding/margin/gap values are multiples of 4px or use spacing variables (code inspection).
- [ ] Amount cells and stat values have `font-variant-numeric: tabular-nums`, and numeric columns in the recent-expenses table are right-aligned with a row hover style (code inspection of `profile.css`).
- [ ] `base.html` loads Lucide from a CDN script tag with a pinned version (not `@latest`) exactly once and calls `lucide.createIcons()`; `profile.html` uses `data-lucide` icons only on section headings and stat cards, and every icon has an adjacent text label (grep / inspection).
- [ ] No React, Vue, Tailwind, Bootstrap, or jQuery is added (grep `templates/` and `static/`); `requirements.txt` is unchanged.
- [ ] `database/db.py` contains `get_expense_summary()`, `get_category_totals()`, `get_recent_expenses()`; every new query uses `?` placeholders and `app.py` contains no SQL strings or `sqlite3` import (code inspection / grep).
- [ ] `requirements.txt` is unchanged and the `/expenses/*` stubs are unchanged.
- [ ] `tests/test_profile.py` exists, uses a temporary database, and `venv\Scripts\python.exe -m pytest` passes with all tests green (including the existing registration and login/logout tests).
- [ ] Manual check: running `venv\Scripts\python.exe app.py`, signing in at `http://127.0.0.1:5001/login` as `demo@spendly.com` / `demo123`, clicking "Profile" in the navbar shows the designed page at `/profile`; resizing the browser to ~360px width stacks the cards vertically with no page-level horizontal scroll, and below ~768px the recent-expenses table scrolls horizontally within its wrapper. With network blocked to the Lucide CDN, the page still renders fully with text labels.
