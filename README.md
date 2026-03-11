# Price Intelligence

A Flask-based price tracking web application that lets users monitor product prices, view price history, and get notified when discounts appear.

## Features

- User authentication with email and password
- OTP verification flow
- Google OAuth login
- Product price scraping from supported product pages
- Track multiple products in one dashboard
- Price history for each tracked item
- Manual discount checks
- Automated background price checks with APScheduler
- Email alerts for real price drops
- CSV report export
- Docker support
- Automated tests

## Tech Stack

- Python
- Flask
- SQLite
- APScheduler
- Authlib
- Flask-Bcrypt
- Flask-Limiter
- BeautifulSoup4
- Requests
- Resend
- HTML / CSS / Jinja2

## Screenshots

### Login Page
<img width="1845" height="954" alt="image" src="https://github.com/user-attachments/assets/70aae050-436c-4c0b-b777-04b075826c6a" />


### Dashboard
<img width="1831" height="954" alt="Screenshot from 2026-03-11 13-58-25" src="https://github.com/user-attachments/assets/bd77acfd-845a-4df1-865c-205e8d5afb1f" />


### Email Price Alert
<img width="828" height="1792" alt="IMG_7494 (1)" src="https://github.com/user-attachments/assets/09861bfe-da83-483e-ba3d-cdbb0c5fa381" />


## How It Works

1. A user registers or logs in.
2. The user adds a product URL to track.
3. The app scrapes product details such as title, image, and price.
4. The product is saved to the user dashboard.
5. The app can check prices manually or automatically in the background.
6. If a real price drop is detected, the user can be notified by email.
7. The user can also export tracked product data as a CSV report.

## Installation

```bash
git clone https://github.com/halilidrilon52-debug/price-intelligence.git
cd price-intelligence
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
