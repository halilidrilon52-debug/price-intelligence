import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-change-this")

    # Email (Gmail SMTP)
    SMTP_CONFIG = {
        "sender_email": os.environ.get("SENDER_EMAIL", "youremail@gmail.com"),
        "sender_password": os.environ.get("SENDER_PASSWORD", "your-app-password")
    }

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # 2FA code expiry (in minutes)
    OTP_EXPIRY_MINUTES = 5
