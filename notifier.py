import resend
import csv
import os
from datetime import datetime

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_email(to_email, subject, html_body, smtp_config=None):
    """Send an HTML email using Resend."""
    try:
        params = {
            "from": "Price Intelligence <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        resend.Emails.send(params)
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False


def send_price_alert(to_email, product, old_price, new_price, smtp_config=None):
    """Send a price drop alert email."""
    discount = round(float(old_price) - float(new_price), 2)
    percent = round((discount / float(old_price)) * 100, 1)

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background:#0f172a; color:white;">
        <h2 style="color: #16a34a;">🎉 Price Drop Alert!</h2>
        <p>Good news! A product you are tracking has dropped in price.</p>
        <hr style="border-color:#334155;">
        <h3>{product['title']}</h3>
        {"<img src='" + str(product['image_url']) + "' width='200' style='border-radius:8px'><br><br>" if product.get('image_url') else ""}
        <p>💰 <b>Old Price:</b> <s>${old_price}</s></p>
        <p>🔥 <b>New Price:</b> <span style="color:#22c55e; font-size:20px;">${new_price}</span></p>
        <p>✅ <b>You save:</b> ${discount} ({percent}% off)</p>
        <br>
        <a href="{product['url']}" style="background:#16a34a; color:white; padding:12px 24px; border-radius:8px; text-decoration:none;">
            Buy Now
        </a>
        <br><br>
        <small style="color:#64748b;">Price Intelligence System — Monitoring prices for you 24/7</small>
    </body>
    </html>
    """

    subject = f"🔥 Price Drop: {product['title']} is now ${new_price}!"
    return send_email(to_email, subject, html_body)


def generate_csv_report(products, output_dir="instance"):
    """Generate a CSV report of all products with price drops."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = os.path.join(output_dir, f"price_report_{timestamp}.csv")

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Product Title", "URL", "Old Price", "New Price", "Discount", "Discount %"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for p in products:
            discount = round(float(p["old_price"]) - float(p["new_price"]), 2)
            percent = round((discount / float(p["old_price"])) * 100, 1)
            writer.writerow({
                "Product Title": p["title"],
                "URL": p["url"],
                "Old Price": p["old_price"],
                "New Price": p["new_price"],
                "Discount": f"${discount}",
                "Discount %": f"{percent}%"
            })

    print(f"✅ CSV report generated: {filename}")
    return filename
