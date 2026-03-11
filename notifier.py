import csv
import logging
import os
from datetime import datetime

import resend


logger = logging.getLogger(__name__)


def send_email(to_email, subject, html_body, smtp_config=None):
    """Send HTML email using Resend."""

    resend.api_key = os.environ.get("RESEND_API_KEY") or resend.api_key

    if not resend.api_key:
        logger.error("RESEND_API_KEY is not set; email not sent.")
        return False

    try:
        params = {
            "from": "Price Intelligence <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }

        resend.Emails.send(params)

        logger.info("Email sent to %s", to_email)
        return True

    except Exception as e:
        logger.exception("Failed to send email: %s", str(e))
        return False


def send_price_alert(to_email, product, old_price, new_price, smtp_config=None):
    """Send email alert when price drops."""

    try:
        old_price = float(old_price)
        new_price = float(new_price)
    except (TypeError, ValueError):
        logger.error("Invalid price values for price alert: %r -> %r", old_price, new_price)
        return False

    if old_price <= 0:
        percent = 0
        discount = 0
    else:
        discount = round(old_price - new_price, 2)
        percent = round((discount / old_price) * 100, 1)

    logger.info(
        "Attempting price alert email to %s for product '%s' (old_price=%s, new_price=%s)",
        to_email,
        product.get("title", "Product"),
        old_price,
        new_price,
    )

    image_html = ""
    if product.get("image_url"):
        image_html = f"""
        <img src="{product['image_url']}"
        width="200"
        style="border-radius:8px;margin-bottom:10px;">
        """

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background:#0f172a; color:white;">
        <h2 style="color:#16a34a;">🎉 Price Drop Alert!</h2>

        <p>A product you are tracking has dropped in price.</p>

        <hr style="border-color:#334155;">

        <h3>{product.get("title","Product")}</h3>

        {image_html}

        <p>💰 <b>Old Price:</b> <s>${old_price}</s></p>
        <p>🔥 <b>New Price:</b> <span style="color:#22c55e;font-size:20px;">${new_price}</span></p>

        <p>✅ <b>You save:</b> ${discount} ({percent}% off)</p>

        <br>

        <a href="{product.get("url","#")}"
           style="background:#16a34a;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;">
            View Product
        </a>

        <br><br>

        <small style="color:#64748b;">
            Price Intelligence System — monitoring prices for you 24/7
        </small>
    </body>
    </html>
    """

    subject = f"🔥 Price Drop: {product.get('title','Product')} is now ${new_price}!"

    sent = send_email(to_email, subject, html_body)

    if sent:
        logger.info("Price alert email successfully sent to %s", to_email)
    else:
        logger.warning("Price alert email NOT sent to %s (send_email returned False)", to_email)

    return sent


def generate_csv_report(products, output_dir="instance"):
    """Generate CSV report for price drops."""

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = os.path.join(output_dir, f"price_report_{timestamp}.csv")

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:

        fieldnames = [
            "Product Title",
            "URL",
            "Old Price",
            "New Price",
            "Discount",
            "Discount %",
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for p in products:

            try:
                old_price = float(p["old_price"])
                new_price = float(p["new_price"])
            except (TypeError, ValueError):
                continue

            discount = round(old_price - new_price, 2)

            if old_price > 0:
                percent = round((discount / old_price) * 100, 1)
            else:
                percent = 0

            writer.writerow({
                "Product Title": p.get("title"),
                "URL": p.get("url"),
                "Old Price": old_price,
                "New Price": new_price,
                "Discount": f"${discount}",
                "Discount %": f"{percent}%",
            })

    logger.info("CSV report generated at %s", filename)

    return filename