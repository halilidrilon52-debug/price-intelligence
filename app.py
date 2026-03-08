from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    send_file,
    flash,
)
from authlib.integrations.flask_client import OAuth
from apscheduler.schedulers.background import BackgroundScheduler
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import DatabaseManager
from scraper import scrape_product
from notifier import send_price_alert, generate_csv_report, send_email
from config import Config
from forms import LoginForm, RegisterForm, OTPForm, ProductForm

import random
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config["WTF_CSRF_ENABLED"] = True

bcrypt = Bcrypt(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

DatabaseManager.init_db()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.check_password_hash(password_hash, password)


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return DatabaseManager.get_user_by_id(user_id)


def generate_otp() -> str:
    return str(random.randint(1000, 9999))


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    user = get_current_user()
    if user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = DatabaseManager.get_user_by_email(email)

        if user and user.get("password_hash") and bcrypt.check_password_hash(
            user["password_hash"], password
        ):
            otp = generate_otp()
            session["otp"] = otp
            session["otp_expiry"] = (datetime.now() + timedelta(minutes=5)).isoformat()
            session["pending_user_id"] = user["id"]

            html = (
                f"<h2>Your verification code is: <b>{otp}</b></h2>"
                "<p>Expires in 5 minutes.</p>"
            )
            send_email(email, "Your Login Code", html)

            # vetëm për development nëse të duhet:
            # print(f"OTP CODE: {otp}")

            flash("Verification code sent to your email.", "info")
            return redirect(url_for("verify_otp"))

        return render_template(
            "login.html",
            form=form,
            error="Invalid email or password.",
        )

    return render_template("login.html", form=form)


@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo:
        flash("Google login failed.", "danger")
        return redirect(url_for("login"))

    email = userinfo["email"]
    google_id = userinfo["sub"]

    user = DatabaseManager.get_user_by_email(email)

    if not user:
        user = DatabaseManager.create_user(
            email=email,
            password_hash=None,
            google_id=google_id,
        )

    if user:
        session["user_id"] = user["id"]
        flash("Logged in successfully with Google.", "success")
        return redirect(url_for("dashboard"))

    flash("Could not complete Google login.", "danger")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        password_hash = hash_password(password)

        user = DatabaseManager.create_user(email, password_hash)

        if user:
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template(
            "register.html",
            form=form,
            error="Email already exists.",
        )

    return render_template("register.html", form=form)


@app.route("/verify", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def verify_otp():
    form = OTPForm()

    if form.validate_on_submit():
        entered_otp = form.otp.data
        stored_otp = session.get("otp")
        expiry = session.get("otp_expiry")
        pending_user_id = session.get("pending_user_id")

        if not stored_otp or not expiry or not pending_user_id:
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("login"))

        if datetime.now() > datetime.fromisoformat(expiry):
            session.pop("otp", None)
            session.pop("otp_expiry", None)
            session.pop("pending_user_id", None)
            return render_template(
                "verify.html",
                form=form,
                error="Code expired. Please login again.",
            )

        if entered_otp == stored_otp:
            session["user_id"] = session.pop("pending_user_id")
            session.pop("otp", None)
            session.pop("otp_expiry", None)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        return render_template(
            "verify.html",
            form=form,
            error="Wrong code. Try again.",
        )

    return render_template("verify.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────────
# Dashboard Routes
# ─────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    products = DatabaseManager.get_user_products(user["id"])
    for p in products:
        p["history"] = DatabaseManager.get_price_history(p["id"])[:5]
    form = ProductForm()

    return render_template(
        "dashboard.html",
        user=user,
        products=products,
        form=form,
    )


@app.route("/add_product", methods=["POST"])
@login_required
def add_product():
    user = get_current_user()
    form = ProductForm()

    if not form.validate_on_submit():
        flash("Please enter a valid product URL.", "danger")
        return redirect(url_for("dashboard"))

    url = form.url.data.strip()
    result = scrape_product(url)

    if not result.get("success"):
        flash("Could not scrape product details from this URL.", "danger")
        return redirect(url_for("dashboard"))

    price = result.get("price")
    if price is None:
        flash("Could not detect product price.", "danger")
        return redirect(url_for("dashboard"))

    DatabaseManager.add_product(
        user_id=user["id"],
        url=url,
        title=result.get("title", "Unknown Product"),
        image_url=result.get("image_url"),
        original_price=price,
    )

    flash("Product added successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/check_prices", methods=["POST"])
@login_required
def check_prices():
    user = get_current_user()
    products = DatabaseManager.get_user_products(user["id"])
    discounted = []

    for product in products:
        result = scrape_product(product["url"])

        if not result.get("success") or result.get("price") is None:
            continue

        new_price = result["price"]
        old_price = product.get("current_price")

        DatabaseManager.add_price_history(product["id"], new_price)
        DatabaseManager.update_product_price(product["id"], new_price)

        if old_price and new_price < old_price:
            discounted.append(
                {
                    "title": product["title"],
                    "url": product["url"],
                    "image_url": product.get("image_url"),
                    "old_price": old_price,
                    "new_price": new_price,
                }
            )
            send_price_alert(
                user["email"],
                product,
                old_price,
                new_price,
            )

    if discounted:
        generate_csv_report(discounted)
        flash(f"Price check completed. {len(discounted)} discounted product(s) found.", "success")
    else:
        flash("Price check completed. No discounts found.", "info")

    return redirect(url_for("dashboard"))


@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    user_id = session["user_id"]
    deleted = DatabaseManager.delete_product(product_id, user_id)

    if deleted:
        flash("Product deleted successfully.", "success")
    else:
        flash("Product not found or not authorized.", "danger")

    return redirect(url_for("dashboard"))


@app.route("/download_report")
@login_required
def download_report():
    os.makedirs("instance", exist_ok=True)

    files = [f for f in os.listdir("instance") if f.startswith("price_report_")]

    if not files:
        user = get_current_user()
        products = DatabaseManager.get_user_products(user["id"])

        if not products:
            flash("No products available to generate a CSV report.", "warning")
            return redirect(url_for("dashboard"))

        # generate a simple CSV report for the current user's products
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"price_report_{timestamp}.csv"
        path = os.path.join("instance", filename)

        import csv

        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Title", "URL", "Original Price", "Current Price"])
            for p in products:
                writer.writerow(
                    [
                        p.get("title"),
                        p.get("url"),
                        p.get("original_price"),
                        p.get("current_price"),
                    ]
                )

        return send_file(path, as_attachment=True)

    latest = sorted(files)[-1]
    return send_file(os.path.join("instance", latest), as_attachment=True)


# ─────────────────────────────────────────────────────────────
# Scheduled Tasks
# ─────────────────────────────────────────────────────────────

def scheduled_price_check():
    products = DatabaseManager.get_all_active_products()
    discounted = []

    for product in products:
        result = scrape_product(product["url"])

        if not result.get("success") or result.get("price") is None:
            continue

        new_price = result["price"]
        old_price = product.get("current_price")

        DatabaseManager.add_price_history(product["id"], new_price)
        DatabaseManager.update_product_price(product["id"], new_price)

        if old_price and new_price < old_price:
            discounted.append(
                {
                    "title": product["title"],
                    "url": product["url"],
                    "image_url": product.get("image_url"),
                    "old_price": old_price,
                    "new_price": new_price,
                }
            )
            send_price_alert(
                product["email"],
                product,
                old_price,
                new_price,
            )

    if discounted:
        generate_csv_report(discounted)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_price_check, trigger="interval", hours=1)
    scheduler.start()
    return scheduler


# ─────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    scheduler = start_scheduler()
    app.run(debug=True,port=5001)