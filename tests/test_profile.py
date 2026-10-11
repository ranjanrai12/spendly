import re
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

import database.db as db

DEMO = {"email": "demo@spendly.com", "password": "demo123"}
OTHER = {"name": "Other User", "email": "other@example.com", "password": "otherpass99"}


def login_demo(client):
    return client.post("/login", data=DEMO)


def set_session(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def make_user(name="New User", email="new@example.com"):
    return db.create_user(name, email, generate_password_hash("password123"))


def add_expense(user_id, amount, category, expense_date, description):
    conn = db.get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, expense_date, description),
        )
        conn.commit()
    finally:
        conn.close()


def profile_html(client):
    response = client.get("/profile")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def current_month():
    return datetime.now().strftime("%Y-%m")


def first_of_month():
    return date.today().replace(day=1).isoformat()


def previous_month_day():
    return (date.today().replace(day=1) - timedelta(days=1)).isoformat()


# ---------------------------------------------------------------- access

def test_profile_requires_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert "Demo User" not in response.get_data(as_text=True)


def test_profile_stale_session_redirects_and_clears(client):
    set_session(client, 99999)
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as sess:
        assert "user_id" not in sess


# ---------------------------------------------------------------- content

def test_profile_shows_demo_user(client):
    login_demo(client)
    html = profile_html(client)
    assert "Demo User" in html
    assert "demo@spendly.com" in html


def test_member_since_from_created_at(client):
    conn = db.get_db()
    try:
        conn.execute(
            "UPDATE users SET created_at = ? WHERE email = ?",
            ("2024-03-15 10:00:00", DEMO["email"]),
        )
        conn.commit()
    finally:
        conn.close()
    login_demo(client)
    assert "Member since March 2024" in profile_html(client)


def test_demo_totals(client):
    login_demo(client)
    html = profile_html(client)
    assert "₹279.84" in html
    assert re.search(r'profile-stat-value">8<', html)


def test_month_total_excludes_other_months(client):
    uid = make_user()
    add_expense(uid, 100.00, "Food", first_of_month(), "this month a")
    add_expense(uid, 23.50, "Bills", first_of_month(), "this month b")
    add_expense(uid, 1000.00, "Other", previous_month_day(), "last month")
    set_session(client, uid)
    html = profile_html(client)
    stat_values = re.findall(r'profile-stat-value">([^<]+)<', html)
    assert stat_values == ["₹1,123.50", "3", "₹123.50"]


def test_category_order_descending(client):
    login_demo(client)
    html = profile_html(client)
    categories = html.split('class="profile-categories"')[1]
    assert categories.index("Bills") < categories.index("Food")


def test_recent_expenses_capped_at_ten_newest_first(client):
    uid = make_user()
    for day in range(1, 13):
        add_expense(uid, float(day), "Food", f"2024-01-{day:02d}", f"item-{day:02d}")
    set_session(client, uid)
    html = profile_html(client)
    tbody = html.split("<tbody>")[1].split("</tbody>")[0]
    assert tbody.count("<tr>") == 10
    assert "item-12" in tbody
    assert "item-03" in tbody
    assert "item-02" not in tbody
    assert "item-01" not in tbody
    assert tbody.index("item-12") < tbody.index("item-03")


def test_null_description_has_no_none(client):
    uid = make_user()
    add_expense(uid, 5.00, "Other", first_of_month(), None)
    set_session(client, uid)
    assert "None" not in profile_html(client)


def test_empty_state_for_user_without_expenses(client):
    set_session(client, make_user())
    html = profile_html(client)
    assert "No expenses yet" in html
    assert html.count("₹0.00") == 2
    assert re.search(r'profile-stat-value">0<', html)


def test_expenses_isolated_between_users(client):
    other_id = db.create_user(
        OTHER["name"], OTHER["email"], generate_password_hash(OTHER["password"])
    )
    add_expense(other_id, 7.77, "Travel", first_of_month(), "other-user-secret")
    login_demo(client)
    assert "other-user-secret" not in profile_html(client)

    set_session(client, other_id)
    html = profile_html(client)
    assert "other-user-secret" in html
    assert "Metro card top-up" not in html


def test_descriptions_are_escaped(client):
    uid = make_user()
    add_expense(uid, 1.00, "Other", first_of_month(), "<script>alert(1)</script>")
    set_session(client, uid)
    html = profile_html(client)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_no_password_hash_exposed(client):
    login_demo(client)
    html = profile_html(client)
    assert "password_hash" not in html
    assert "pbkdf2:" not in html
    assert "scrypt:" not in html
    user = db.get_user_by_id(db.get_user_by_email(DEMO["email"])["id"])
    assert "password_hash" not in user.keys()
    assert "created_at" in user.keys()


# ---------------------------------------------------------------- navbar

def test_navbar_profile_link_when_logged_in(client):
    login_demo(client)
    html = client.get("/").get_data(as_text=True)
    assert 'class="nav-profile"' in html
    assert 'href="/profile"' in html
    assert "Sign out" in html


def test_navbar_no_profile_link_when_logged_out(client):
    html = client.get("/").get_data(as_text=True)
    assert 'class="nav-profile"' not in html
    assert "Sign out" not in html


# ---------------------------------------------------------------- db helpers

def test_summary_zeros_for_unknown_user(client):
    summary = db.get_expense_summary(99999, current_month())
    assert summary == {"total": 0.0, "count": 0, "month_total": 0.0}


def test_category_totals_ordering(client):
    uid = make_user()
    add_expense(uid, 10, "B", first_of_month(), None)
    add_expense(uid, 10, "A", first_of_month(), None)
    add_expense(uid, 50, "C", first_of_month(), None)
    rows = db.get_category_totals(uid)
    assert [r["category"] for r in rows] == ["C", "A", "B"]
