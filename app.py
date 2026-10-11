import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    DuplicateEmailError,
    create_user,
    get_category_totals,
    get_db,
    get_expense_summary,
    get_recent_expenses,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

app = Flask(__name__)

# DEVELOPMENT ONLY: publicly known fallback so local runs work without setup.
# Never used when SPENDLY_ENV=production (startup fails instead).
_DEV_ONLY_SECRET_KEY = "spendly-development-only-not-a-secret"

_secret_key = os.environ.get("SPENDLY_SECRET_KEY", "").strip()
if os.environ.get("SPENDLY_ENV", "development").strip().lower() == "production" and not _secret_key:
    raise RuntimeError("SPENDLY_SECRET_KEY must be set when SPENDLY_ENV=production")
app.secret_key = _secret_key or _DEV_ONLY_SECRET_KEY

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Template filters (presentation only)                                #
# ------------------------------------------------------------------ #

@app.template_filter("rupee")
def rupee(value):
    return f"₹{(value or 0):,.2f}"


def _parse_date(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except ValueError:
        return None


@app.template_filter("pretty_date")
def pretty_date(value):
    parsed = _parse_date(value)
    return parsed.strftime("%d %b %Y") if parsed else (value or "")


@app.template_filter("month_year")
def month_year(value):
    parsed = _parse_date(value)
    return parsed.strftime("%B %Y") if parsed else (value or "")


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


MIN_PASSWORD_LENGTH = 8


def validate_registration(name, email, password, confirm_password):
    if not name:
        return "Please enter your name."
    local, sep, domain = email.partition("@")
    if not (local and sep and domain):
        return "Please enter a valid email address."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if password != confirm_password:
        return "Passwords do not match."
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    error = validate_registration(name, email, password, confirm_password)
    if error is None and get_user_by_email(email) is not None:
        error = "An account with that email already exists."
    if error is None:
        try:
            create_user(name, email, generate_password_hash(password))
        except DuplicateEmailError:
            error = "An account with that email already exists."
    if error:
        return render_template("register.html", error=error, name=name, email=email)

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email) if email else None
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", error="Invalid email or password.", email=email
        )

    session.clear()
    session["user_id"] = int(user["id"])
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    month = datetime.now().strftime("%Y-%m")
    return render_template(
        "profile.html",
        user=user,
        summary=get_expense_summary(user_id, month),
        categories=get_category_totals(user_id),
        expenses=get_recent_expenses(user_id),
    )


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
