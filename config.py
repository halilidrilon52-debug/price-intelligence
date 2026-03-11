import os

from dotenv import load_dotenv


# Load environment variables from a .env file if present.
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # ─────────────────────────────────────────────
    # Flask
    # ─────────────────────────────────────────────

    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in environment variables")

    # ─────────────────────────────────────────────
    # Resend Email API
    # ─────────────────────────────────────────────

    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

    # ─────────────────────────────────────────────
    # Google OAuth
    # ─────────────────────────────────────────────

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # ─────────────────────────────────────────────
    # OTP
    # ─────────────────────────────────────────────

    OTP_EXPIRY_MINUTES = 5

    # ─────────────────────────────────────────────
    # Paths
    # ─────────────────────────────────────────────

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    DATABASE_PATH = os.path.join(INSTANCE_DIR, "price_intel.db")

    # ─────────────────────────────────────────────
    # App Settings
    # ─────────────────────────────────────────────

    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"