import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import traceback
from email.message import EmailMessage
from groq import Groq

# ── Secrets ──────────────────────────────────────────────
GROQ_KEY      = os.environ.get("GROQ_API_KEY", "")
GMAIL_PASS    = os.environ.get("GMAIL_APP_PASSWORD", "")
BLOGGER_MAIL  = os.environ.get("BLOGGER_EMAIL", "")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "")
SENDER_GMAIL  = os.environ.get("SENDER_GMAIL", "")
SENDER_PASS   = os.environ.get("SENDER_GMAIL_PASS", "")

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = str(datetime.date.today().year)

# ── Topic Rotation System ─────────────────────────────────
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year} — cover its benchmarks, real-world impact",
    f"a BREAKTHROUGH scientific study published in {current_year} reshaping human cognition using technology",
    f"a revolutionary AI-powered tool JUST LAUNCHED for students in {current_year} changing how people study",
    f"a major SILICON VALLEY corporate acquisition happening RIGHT NOW in {current_year}",
    f"a cutting-edge AI application in healthcare that produced landmark results in {current_year}",
    f"the fierce battle between AI giants OpenAI vs Google over a specific capability in {current_year}",
    f"how a newly released AI coding tool in {current_year} is transforming software engineering",
    f"a viral AI use case that regular people are adopting RIGHT NOW in {current_year}",
]

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt Construction ──────────────────────────────────
prompt = f"""
Current Date: {today_date}
You are a Pulitzer Prize-winning investigative tech journalist.
YOUR ASSIGNED STORY: {chosen_topic}

ABSOLUTE RULES:
1. NO generic advice.
2. BREAKING NEWS style.
3. Invent realistic details, quotes, and names.
4. Min 900 words, Max 1200 words.
5. HTML Structure: <p>, <h2>, <strong>, <em>, <blockquote>.

[TITLE] headline under 65 chars
[KEYWORDS] keywords here
[META] description here
[CONTENT] HTML body
"""

# ── CSS ──────────────────────────────────────────────────
CSS = """
  body { font-family: Georgia, serif; background: #fafaf8; color: #0d0d0d; line-height: 1.75; padding: 20px; }
  .article-wrap { max-width: 700px; margin: auto; background: white; padding: 40px; border: 1px solid #ddd; }
  h1 { font-family: 'Playfair Display', serif; font-size: 36px; margin-bottom: 20px; }
  h2 { border-bottom: 2px solid #0d0d0d; margin-top: 40px; }
  blockquote { border-left: 4px solid #c0392b; padding: 10px 20px; font-style: italic; background: #fff8f7; }
  .featured-image { width: 100%; height: auto; margin-bottom: 30px; }
"""

def parse_response(raw):
    raw = str(raw)
    title_match = re.search(r"\[TITLE\](.*?)(?=\[KEYWORDS\]|\[META\]|\[CONTENT\]|$)", raw, re.IGNORECASE | re.DOTALL)
    kw_match    = re.search(r"\[KEYWORDS\](.*?)(?=\[META\]|\[CONTENT\]|\[TITLE\]|$)", raw, re.IGNORECASE | re.DOTALL)
    meta_match  = re.search(r"\[META\](.*?)(?=\[CONTENT\]|\[TITLE\]|\[KEYWORDS\]|$)", raw, re.IGNORECASE | re.DOTALL)
    content_match = re.search(r"\[CONTENT\](.*)", raw, re.IGNORECASE | re.DOTALL)

    title    = title_match.group(1).strip() if title_match else f"Tech Update: {today_date}"
    keywords = kw_match.group(1).strip() if kw_match else "AI, Tech"
    meta     = meta_match.group(1).strip() if meta_match else "AI news"
    content  = content_match.group(1).strip() if content_match else ""
    
    return str(title), str(keywords), str(meta), str(content)

def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/628"
    try:
        query = urllib.parse.quote(str(keywords))
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        data = res.json()
        if data.get("photos"): return data["photos"][0]["src"]["large2x"]
    except: pass
    return "https://picsum.photos/1200/628"

def build_html(title, meta_desc, image_url, article_body):
    # استخدام f-strings يمنع خطأ الـ bytes vs str نهائياً
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>{CSS}</style>
    </head>
    <body>
        <div class="article-wrap">
            <p style="text-transform:uppercase; color:#c0392b; font-weight:bold;">Exclusive Report</p>
            <h1>{title}</h1>
            <p><em>By Smart Flow Lab Editorial Team | {today_date}</em></p>
            <img src="{image_url}" class="featured-image">
            <div class="content">
                {article_body}
            </div>
        </div>
    </body>
    </html>
    """

def send_email(title, html_body):
    try:
        msg = EmailMessage()
        msg["Subject"] = str(title)
        msg["From"]    = str(SENDER_GMAIL)
        msg["To"]      = str(BLOGGER_MAIL)
        msg.set_content("HTML content required.")
        msg.add_alternative(str(html_body), subtype="html")

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(str(SENDER_GMAIL), str(SENDER_PASS))
            server.send_message(msg)
        print(f"SUCCESS: Published '{title}'")
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

def main():
    print(f"Targeting: {chosen_topic}")
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        raw_res = completion.choices[0].message.content
        title, keywords, meta, body = parse_response(raw_res)
        
        img_url = get_best_pexels_image(keywords)
        full_html = build_html(title, meta, img_url, body)
        
        send_email(title, full_html)
    except Exception as e:
        print(f"Main Loop Error: {e}")

if __name__ == "__main__":
    main()
