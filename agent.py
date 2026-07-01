import anthropic
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

# --- CONFIG ---
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]
RECIPIENT_EMAIL_CHINA = os.environ["RECIPIENT_EMAIL_CHINA"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

almaty_tz = timezone(timedelta(hours=5))
now = datetime.now(almaty_tz)
today_str = now.strftime("%d %B %Y")
week_start = now.strftime("%d %B")
week_end = (now + timedelta(days=6)).strftime("%d %B %Y")


def get_holidays(region_name, region_desc):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Today is {today_str}.
Find significant holidays and festivals in {region_desc} for the upcoming week ({week_start} – {week_end}).

For each significant holiday found, provide:
📅 Name and date
🌍 Country / region
📖 What is this holiday — briefly
🎨 Visual features — colors, costumes, decor, food
📱 Content potential — why it will work on Reels/Instagram
💡 Video idea — one specific idea

Criteria for "significant":
- National and state holidays
- Mass festivals with high visual component (like Diwali, Holi, Eid)
- Events with viral potential — millions of people doing the same thing simultaneously
- Bright visuals — colors, costumes, food, decor
- Family and community traditions

NOT significant:
- Local regional holidays of small cities
- Official dates without real public celebration
- Political and state ceremonies without visual content

If no significant holidays found for this week, write: "No significant holidays this week."

Write in Russian."""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        messages=[{"role": "user", "content": prompt}]
    )

    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text
    return result


def send_email(recipient, subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = recipient
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, recipient, msg.as_string())
    print(f"✅ Email sent to {recipient}")


def main():
    print(f"🔍 Searching holidays for {week_start} – {week_end}...")

    print("  → India...")
    india = get_holidays("India", "India")

    print("  → MENA...")
    mena = get_holidays("MENA", "Middle East and North Africa (MENA region)")

    print("  → China...")
    china = get_holidays("China", "China")

    # Email 1: India + MENA → ar1@bafid.com
    body_india_mena = f"""🌏 HOLIDAY DIGEST — {week_start} – {week_end}
Праздники Индии и региона MENA на предстоящую неделю

{'='*50}
🇮🇳 ИНДИЯ
{'='*50}
{india}

{'='*50}
🌙 MENA (Ближний Восток и Северная Африка)
{'='*50}
{mena}

---
Дайджест подготовлен автоматически агентом holiday-digest
"""

    # Email 2: China → ua@bafid.com
    body_china = f"""🌏 HOLIDAY DIGEST — {week_start} – {week_end}
Праздники Китая на предстоящую неделю

{'='*50}
🇨🇳 КИТАЙ
{'='*50}
{china}

---
Дайджест подготовлен автоматически агентом holiday-digest
"""

    print("✉️  Building and sending emails...")
    send_email(RECIPIENT_EMAIL, f"🗓 Holiday Digest: Индия & MENA — {week_start}–{week_end}", body_india_mena)
    send_email(RECIPIENT_EMAIL_CHINA, f"🗓 Holiday Digest: Китай — {week_start}–{week_end}", body_china)
    print("✅ Done!")


if __name__ == "__main__":
    main()
