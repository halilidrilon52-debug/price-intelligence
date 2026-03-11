import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT_SECONDS = 10


def extract_price(text: Optional[str]) -> Optional[float]:
    """
    Extract numeric price from strings like:
    $29.99
    29,99 €
    1,299.99
    1.299,99
    """

    if not text:
        return None

    cleaned = re.sub(r"[^\d.,]", "", text.strip())
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        # detect decimal separator
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_product(url: str) -> dict:
    """
    Scrape product title, image and price from a product page.
    """

    try:
        with requests.Session() as session:
            response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # ───────── TITLE ─────────
        title = None

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.text.strip()

        if not title:
            title = "Unknown Product"

        # ───────── IMAGE ─────────
        image_url = None

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            image_url = og_image["content"]

        # ───────── PRICE ─────────
        price = None

        # product price meta
        price_meta = soup.find("meta", property="product:price:amount")
        if price_meta:
            price = extract_price(price_meta.get("content"))

        # og price
        if price is None:
            og_price = soup.find("meta", property="og:price:amount")
            if og_price:
                price = extract_price(og_price.get("content"))

        # common price classes
        if price is None:
            price_tags = soup.find_all(
                ["span", "div", "p"],
                class_=re.compile(r"(price|amount|cost)", re.I)
            )

            for tag in price_tags:
                price = extract_price(tag.get_text())
                if price:
                    break

        return {
            "title": title,
            "image_url": image_url,
            "price": price,
            "success": True,
        }

    except requests.exceptions.RequestException as e:
        return {
            "title": None,
            "image_url": None,
            "price": None,
            "success": False,
            "error": f"Request error: {str(e)}",
        }

    except Exception as e:
        return {
            "title": None,
            "image_url": None,
            "price": None,
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    url = input("Enter product URL: ")
    result = scrape_product(url)
    print(result)