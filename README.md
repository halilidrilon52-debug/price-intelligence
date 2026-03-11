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

![IMG_7477](https://github.com/user-attachments/assets/7eb82964-22e6-42a6-9f41-fd02cc911d2d)


### Dashboard

<img width="1843" height="967" alt="Screenshot from 2026-03-11 13-22-53" src="https://github.com/user-attachments/assets/0ccf8cd8-88a4-47a7-8224-b70a690ecb21" />


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
