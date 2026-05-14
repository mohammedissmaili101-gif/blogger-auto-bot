import os
import smtplib
import re
import datetime
import urllib.parse
import requests
from email.mime.text import MIMEText
from groq import Groq

# ── Secrets ──────────────────────────────────────────────
GROQ_KEY     = os.environ.get("GROQ_API_KEY")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

client     = Groq(api_key=GROQ_KEY)
today_date = datetime.date.today().strftime("%B %d, %2026")
today_year = 2026

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}
You are a Pulitzer-level investigative tech journalist writing for Wired Magazine.
TASK: Write one EXCLUSIVE investigative tech article ({today_year} only).

═══ STRUCTURE ═══
TITLE: [max 70 chars]
SLUG_KEYWORDS: [3-5 specific visual English words for Pexels]
FALLBACK_KEYWORDS: [3-5 alternative keywords]
META_DESC: [150-155 chars]
CONTENT: [HTML using ONLY: <p> <h2> <h3> <blockquote> <strong> <em>]

Minimum 1000 words. Be human, passionate, and analytical.
"""

def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=3500,
        )
        raw = completion.choices[0].message.content

        # استخراج البيانات مع حماية ضد الـ None
        title = re.search(r"TITLE:\s*(.*)", raw)
        title = title.group(1).strip() if title else "Tech Innovation 2026"

        slug_kw = re.search(r"SLUG_KEYWORDS:\s*(.*)", raw)
        slug_kw = slug_kw.group(1).strip() if slug_kw else "technology future"

        meta_desc = re.search(r"META_DESC:\s*(.*)", raw)
        meta_desc = meta_desc.group(1).strip() if meta_desc else "Latest tech news from Smart Flow Lab."

        fallback_kw = re.search(r"FALLBACK_KEYWORDS:\s*(.*)", raw)
        fallback_kw = fallback_kw.group(1).strip() if fallback_kw else "digital innovation"

        if "CONTENT:" in raw:
            content = raw.split("CONTENT:")[1].strip()
        else:
            content = "<p>Content generation in progress...</p>"

        return title, slug_kw, fallback_kw, meta_desc, content
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None, None, None, None

# ── Pexels Logic ──────────────────────────────────────────
def get_best_pexels_image(primary_kw, fallback_kw):
    if not PEXELS_KEY:
        return f"https://picsum.photos/seed/{urllib.parse.quote(primary_kw)}/1200/630"
    
    headers = {"Authorization": PEXELS_KEY}
    try:
        # البحث الأول
        res = requests.get(f"https://api.pexels.com/v1/search?query={primary_kw}&per_page=1&orientation=landscape", headers=headers, timeout=10)
        data = res.json()
        if data.get("photos"):
            return data["photos"][0]["src"]["large2x"]
        
        # البحث الثاني (fallback)
        res = requests.get(f"https://api.pexels.com/v1/search?query={fallback_kw}&per_page=1&orientation=landscape", headers=headers, timeout=10)
        data = res.json()
        if data.get("photos"):
            return data["photos"][0]["src"]["large2x"]
            
    except Exception as e:
        print(f"⚠️ Pexels error: {e}")
    
    return f"https://picsum.photos/seed/tech/1200/630"

# ── Build & Send ──────────────────────────────────────────
title, slug_kw, fallback_kw, meta_desc, article_body = generate_content()

if title and article_body:
    image_url = get_best_pexels_image(slug_kw, fallback_kw)
    
    full_html = f"""
    <html>
    <head><meta name="description" content="{meta_desc}"></head>
    <body style="font-family: 'Georgia', serif; line-height: 1.6; max-width: 800px; margin: auto; padding: 20px;">
        <h1 style="font-family: Arial, sans-serif; font-size: 40px;">{title}</h1>
        <p style="color: #666;">Published on {today_date} by Smart Flow Lab</p>
        <img src="{image_url}" style="width: 100%; border-radius: 10px; margin: 20px 0;">
        <div class="content">{article_body}</div>
        <hr>
        <p style="text-align: center; color: #999;">© 2026 Smart Flow Lab - Tech Journalism</p>
    </body>
    </html>
    """

    msg = MIMEText(full_html, 'html', 'utf-8')
    msg['Subject'] = f"{title} #News"
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Success: {title}")
    except Exception as e:
        print(f"❌ Mail Error: {e}")
