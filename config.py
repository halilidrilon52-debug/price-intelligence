import os
from dotenv import load_dotenv

load_dotenv()


class Config:
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
    # App Settings
    # ─────────────────────────────────────────────

    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"