import anthropic
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

# --- CONFIG ---
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

almaty_tz = timezone(timedelta(hours=5))
now = datetime.now(almaty_tz)
today_str = now.strftime("%d %B %Y")
week_start = now.strftime("%d %B")
week_end = (now + timedelta(days=6)).strftime("%d %B %Y")


def get_holidays(region_name, region_desc):
    """Search for significant holidays in the upcoming week for a region."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Today is {today_str}. You are a content strategist for a lifestyle brand on Instagram and Reels.

Search the web for significant holidays, festivals, and celebrations in {region_desc}
happening in the next 7 days ({week_start} – {week_end}).

WHAT COUNTS AS SIGNIFICANT:
- National and state holidays with mass public participation
- Religious festivals celebrated by large numbers of people (Eid, Diwali, Holi, etc.)
- Festivals with strong visual potential — colors, costumes, food, decorations, rituals
- Events where millions of people do the same thing simultaneously
- Culturally fascinating traditions that would surprise or delight a global audience

WHAT TO SKIP:
- Small local or regional observances with no visual content potential
- Official state ceremonies without public participation
- Political or government events
- Anything related to conflict, mourning, or controversy

For each significant holiday found, write EXACTLY in this format:

==={region_name}===

🗓 [HOLIDAY NAME] — [DATE]
🌍 [Country or sub-region]

📖 WHAT IS IT:
[2-3 sentences explaining the holiday — origin, meaning, who celebrates it]

🎨 VISUAL HIGHLIGHTS:
[Describe colors, costumes, decorations, food, rituals — what would the camera see]

📱 CONTENT POTENTIAL:
[Why this would perform well on Instagram/Reels — shareability, wow-factor, relatability]

💡 VIDEO IDEA:
[One specific, concrete video concept for a lifestyle brand]

---

[next holiday if exists]

===END===

If no significant holidays found this week, write:
==={region_name}===
No significant holidays this week.
===END===

Start directly with ==={region_name}===. No preamble."""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    result = ""
    for block in response.content:
        if block.type == "text":
            result += block.text
    return result


def parse_region(raw, region_name):
    lines = raw.splitlines()
    content = []
    inside = False
    for line in lines:
        if line.strip() == f"==={region_name}===":
            inside = True
            continue
        elif line.strip() == "===END===":
            inside = False
            break
        elif inside:
            content.append(line)
    return "\n".join(content).strip()


def build_email(india, mena):
    body = f"""WEEKLY HOLIDAY DIGEST | ПРАЗДНИЧНЫЙ ДАЙДЖЕСТ
Week: {week_start} – {week_end}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇮🇳 INDIA | ИНДИЯ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{india}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 MENA (Middle East & North Africa) | БЛИЖНИЙ ВОСТОК И СЕВЕРНАЯ АФРИКА
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{mena}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated automatically | Сформировано автоматически
Holiday Digest Agent · Almaty UTC+5 · Every Monday 8:00 AM
"""
    return body


def send_email(body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎉 Holiday Digest — {week_start}–{week_end} | India & MENA"
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    print(f"🔍 Searching holidays for {week_start} – {week_end}...")

    print("  → India...")
    raw_india = get_holidays("INDIA", "India")
    india = parse_region(raw_india, "INDIA")

    print("  → MENA...")
    raw_mena = get_holidays("MENA", "the Middle East and North Africa (MENA region)")
    mena = parse_region(raw_mena, "MENA")

    print("✉️  Building and sending email...")
    body = build_email(india, mena)
    send_email(body)
    print("✅ Done!")
