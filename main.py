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
# استعملت التاريخ الحالي ديال 2026 كيفما طلبتي
today_date = datetime.date.today().strftime("%B %d, %Y")
current_year = 2026

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}
You are an elite tech journalist. Write a 1000-word EXCLUSIVE investigative report on a tech breakthrough in {current_year}.
FORMAT:
[TITLE] Catchy journalistic title.
[KEYWORDS] 3-4 visual words.
[META] 150-char SEO description.
[CONTENT] Full HTML article. Use <h2>, <p>, <blockquote>, <strong>. No markdown.
"""

def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=4000,
        )
        raw = completion.choices[0].message.content

        # Extraction using Regex
        title_search = re.search(r"\[TITLE\](.*?)\[", raw, re.S | re.I)
        kw_search = re.search(r"\[KEYWORDS\](.*?)\[", raw, re.S | re.I)
        meta_search = re.search(r"\[META\](.*?)\[", raw, re.S | re.I)
        content_search = re.search(r"\[CONTENT\](.*)", raw, re.S | re.I)

        title = title_search.group(1).strip() if title_search else "Tech Evolution 2026"
        keywords = kw_search.group(1).strip() if kw_search else "future technology"
        # تم إصلاح القوس الزائد هنا
        meta = meta_search.group(1).strip() if meta_search else "Exclusive look at the future of tech."
        
        if content_search:
            article = content_search.group(1).strip()
            article = article.replace("```html", "").replace("
```", "").strip()
        else:
            return None, None, None, None

        return title, keywords, meta, article
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None, None, None

def get_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    try:
        url = f"https://api.pexels.com/v1/search?query={keywords}&per_page=1&orientation=landscape"
        r = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        return r.json()['photos'][0]['src']['large2x']
    except:
        return f"https://picsum.photos/seed/{urllib.parse.quote(keywords)}/1200/630"

# ── Build & Send ──────────────────────────────────────────
t, k, m, body = generate_content()

if t and body:
    img = get_pexels_image(k)
    
    # استعملت f-strings عادية لتفادي مشاكل الأقواس في القالب
    full_html = f"""
    <html>
    <head><meta name="description" content="{m}"></head>
    <body style="font-family: 'Segoe UI', sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: auto; padding: 20px;">
        <span style="color: #1a73e8; font-weight: bold; text-transform: uppercase;">Exclusive Report</span>
        <h1 style="font-size: 38px; margin-top: 10px;">{t}</h1>
        <p style="color: #777; border-bottom: 1px solid #eee; padding-bottom: 15px;">Smart Flow Lab | {today_date}</p>
        <img src="{img}" style="width: 100%; border-radius: 12px; margin: 20px 0;">
        <div style="font-size: 19px;">{body}</div>
        <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #aaa;">© {current_year} Smart Flow Lab</div>
    </body>
    </html>
    """

    msg = MIMEText(full_html, 'html', 'utf-8')
    msg['Subject'] = t
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published: {t}")
    except Exception as e:
        print(f"❌ Mail Error: {e}")
