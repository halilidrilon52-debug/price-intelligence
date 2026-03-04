from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from authlib.integrations.flask_client import OAuth
from apscheduler.schedulers.background import BackgroundScheduler
from database import DatabaseManager, get_db_connection
from scraper import scrape_product
from notifier import send_price_alert, generate_csv_report
from config import Config

from forms import LoginForm, RegisterForm, OTPForm, ProductForm

# security & forms
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# load_dotenv() called previously

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
# enable CSRF with Flask-WTF (uses SECRET_KEY)
app.config['WTF_CSRF_ENABLED'] = True

# extensions
bcrypt = Bcrypt(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# Google OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

# Initialize database on startup
DatabaseManager.init_db()

# ─── Helper Functions ─────────────────────────────────────────────────────────

# password helpers using bcrypt

def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return bcrypt.generate_password_hash(password).decode('utf-8')


def check_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return bcrypt.check_password_hash(password_hash, password)

def get_current_user():
    if "user_id" not in session:
        return None
    return DatabaseManager.get_user_by_id(session["user_id"])

def generate_otp():
    return str(random.randint(1000, 9999))

# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    user = get_current_user()
    if user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # simple rate limit to slow brute force
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = DatabaseManager.get_user_by_email(email)

        if user and user.get("password_hash") and check_password(password, user["password_hash"]):
            otp = generate_otp()
            session["otp"] = otp
            session["otp_expiry"] = (datetime.now() + timedelta(minutes=5)).isoformat()
            session["pending_user_id"] = user["id"]

            from notifier import send_email
            html = f"<h2>Your verification code is: <b>{otp}</b></h2><p>Expires in 5 minutes.</p>"
            send_email(email, "Your Login Code", html)
            print(f"========= OTP CODE: {otp} =========")

            return redirect(url_for("verify_otp"))
        else:
            return render_template("login.html", form=form, error="Invalid email or password.")

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
        return redirect(url_for("login"))

    email = userinfo["email"]
    google_id = userinfo["sub"]

    # Check if user exists
    user = DatabaseManager.get_user_by_email(email)

    if not user:
        # Create new user with Google
        user = DatabaseManager.create_user(email, password_hash=None, google_id=google_id)

    if user:
        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))

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
            return redirect(url_for("login"))
        else:
            return render_template("register.html", form=form, error="Email already exists.")

    return render_template("register.html", form=form)

@app.route("/verify", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def verify_otp():
    form = OTPForm()
    if form.validate_on_submit():
        entered_otp = form.otp.data
        stored_otp = session.get("otp")
        expiry = session.get("otp_expiry")

        if not stored_otp or not expiry:
            return redirect(url_for("login"))

        if datetime.now() > datetime.fromisoformat(expiry):
            return render_template("verify.html", form=form, error="Code expired. Please login again.")

        if entered_otp == stored_otp:
            session["user_id"] = session.pop("pending_user_id")
            session.pop("otp", None)
            session.pop("otp_expiry", None)
            return redirect(url_for("dashboard"))
        else:
            return render_template("verify.html", form=form, error="Wrong code. Try again.")

    return render_template("verify.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── Dashboard Routes ─────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    products = DatabaseManager.get_user_products(user["id"])
    form = ProductForm()
    return render_template("dashboard.html", user=user, products=products, form=form)

@app.route("/add_product", methods=["POST"])
def add_product():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    form = ProductForm()
    if not form.validate_on_submit():
        return redirect(url_for("dashboard"))

    url = form.url.data
    result = scrape_product(url)

    if not result["success"]:
        return redirect(url_for("dashboard"))

    DatabaseManager.add_product(
        user_id=user["id"],
        url=url,
        title=result["title"],
        image_url=result["image_url"],
        original_price=result["price"]
    )

    return redirect(url_for("dashboard"))

@app.route("/check_prices")
def check_prices():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    products = DatabaseManager.get_user_products(user["id"])
    discounted = []

    for product in products:
        result = scrape_product(product["url"])
        if not result["success"] or not result["price"]:
            continue

        new_price = result["price"]
        old_price = product["current_price"]

        DatabaseManager.add_price_history(product["id"], new_price)
        DatabaseManager.update_product_price(product["id"], new_price)

        if old_price and new_price < old_price:
            discounted.append({
                "title": product["title"],
                "url": product["url"],
                "image_url": product["image_url"],
                "old_price": old_price,
                "new_price": new_price
            })
            send_price_alert(user["email"], product, old_price, new_price, Config.SMTP_CONFIG)

    if discounted:
        generate_csv_report(discounted)

    return redirect(url_for("dashboard"))

@app.route("/delete_product/<int:product_id>")
def delete_product(product_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    DatabaseManager.delete_product(product_id)
    return redirect(url_for("dashboard"))

@app.route("/download_report")
def download_report():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    files = [f for f in os.listdir("instance") if f.startswith("price_report_")]
    if not files:
        return redirect(url_for("dashboard"))

    latest = sorted(files)[-1]
    return send_file(os.path.join("instance", latest), as_attachment=True)

# ─── Scheduled Tasks ─────────────────────────────────────────────────────────

def scheduled_price_check():
    """Background job that scrapes all active products and sends alerts when prices drop."""
    products = DatabaseManager.get_all_active_products()
    discounted = []

    for product in products:
        result = scrape_product(product["url"])
        if not result.get("success") or not result.get("price"):
            continue

        new_price = result["price"]
        old_price = product.get("current_price")

        DatabaseManager.add_price_history(product["id"], new_price)
        DatabaseManager.update_product_price(product["id"], new_price)

        if old_price and new_price < old_price:
            discounted.append({
                "title": product["title"],
                "url": product["url"],
                "image_url": product.get("image_url"),
                "old_price": old_price,
                "new_price": new_price
            })
            # send alert email to owner
            send_price_alert(product["email"], product, old_price, new_price, Config.SMTP_CONFIG)

    if discounted:
        generate_csv_report(discounted)


# Start scheduler when app boots
scheduler = BackgroundScheduler()
# run every hour
scheduler.add_job(func=scheduled_price_check, trigger="interval", hours=1)
scheduler.start()

# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
