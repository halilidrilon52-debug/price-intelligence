# Price Intelligence

A Flask-based web application for tracking product prices, monitoring price changes, and sending alerts.

## Features

- User authentication and login
- Add and manage tracked products
- Automatic price checking
- Email notifications for price changes
- CSV report generation
- PostgreSQL database support
- Docker support
- Basic test suite

## Tech Stack

- Python
- Flask
- PostgreSQL
- BeautifulSoup
- Docker
- HTML/CSS
- Pytest

## Project Structure

- `app.py` - main Flask app
- `database.py` - database operations
- `scraper.py` - price scraping logic
- `notifier.py` - email notifications
- `forms.py` - Flask forms
- `templates/` - HTML templates
- `static/` - static assets
- `tests/` - test files

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/price-intelligence.git
cd price-intelligence
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
# price-intelligence
