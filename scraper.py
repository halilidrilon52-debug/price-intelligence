import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def extract_price(text):
    """Extract numeric price from a string like '$29.99' or '29,99 €'"""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text)
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None

def scrape_product(url):
    """
    Scrape product info from any modern website using Open Graph meta tags.
    Returns a dictionary with title, image, and price.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = None
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content")
        if not title:
            title_tag = soup.find("title")
            title = title_tag.text.strip() if title_tag else "Unknown Product"

        # Extract image
        image_url = None
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image_url = og_image.get("content")

        # Extract price
        price = None
        price_meta = soup.find("meta", property="product:price:amount")
        if price_meta:
            price = extract_price(price_meta.get("content"))

        if not price:
            og_price = soup.find("meta", property="og:price:amount")
            if og_price:
                price = extract_price(og_price.get("content"))

        if not price:
            for tag in soup.find_all(["span", "div", "p"], class_=re.compile(r"price", re.I)):
                price = extract_price(tag.get_text())
                if price:
                    break

        return {
            "title": title,
            "image_url": image_url,
            "price": price,
            "success": True
        }

    except Exception as e:
        return {
            "title": None,
            "image_url": None,
            "price": None,
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    test_url = input("Enter a product URL to test: ")
    result = scrape_product(test_url)
    print(result)
