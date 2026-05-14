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

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %2026")
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
        title_match = re.search(r"\[TITLE\](.*?)\[", raw, re.S | re.I)
        kw_match    = re.search(r"\[KEYWORDS\](.*?)\[", raw, re.S | re.I)
        meta_match   = re.search(r"\[META\](.*?)\[", raw, re.S | re.I)
        content_match = re.search(r"\[CONTENT\](.*)", raw, re.S | re.I)

        title    = title_match.group(1).strip() if title_match else "Tech Evolution 2026"
        keywords = kw_match.group(1).strip() if kw_match else "future technology"
        meta     = meta_match.group(1).strip() if meta_match else "Exclusive look at the future of tech."
        
        if content_match:
            article = content_match.group(1).strip()
            # إصلاح نهائي ومنظم لتنظيف الكود بلا مشاكل Syntax
            article = article.replace('```html', '').replace('
```', '').strip()
        else:
            return None, None, None, None

        return title, keywords, meta, article
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None, None, None

def get_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    try:
        query = urllib.parse.quote(keywords)
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape"
        r = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        data = r.json()
        if 'photos' in data and len(data['photos']) > 0:
            return data['photos'][0]['src']['large2x']
    except Exception as e:
        print(f"⚠️ Pexels error: {e}")
    
    return f"https://picsum.photos/seed/{urllib.parse.quote(keywords)}/1200/630"

# ── Build & Send ──────────────────────────────────────────
t, k, m, body = generate_content()

if t and body:
    img_url = get_pexels_image(k)
    
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="description" content="{m}">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.8; color: #333; max-width: 850px; margin: 0 auto; padding: 30px;">
    <header>
        <strong style="color: #1a73e8; text-transform: uppercase; letter-spacing: 1px;">Exclusive Tech Report</strong>
        <h1 style="font-size: 42px; margin-top: 10px; line-height: 1.2; color: #111;">{t}</h1>
        <p style="color: #666; font-size: 14px; border-bottom: 2px solid #f4f4f4; padding-bottom: 20px;">By Smart Flow Lab | {today_date}</p>
    </header>
    
    <main>
        <img src="{img_url}" alt="Feature Image" style="width: 100%; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
        <div style="font-size: 20px; color: #444; text-align: justify;">
            {body}
        </div>
    </main>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 13px;">
        © {current_year} Smart Flow Lab - Digital Intelligence Hub
    </footer>
</body>
</html>"""

    msg = MIMEText(full_html, 'html', 'utf-8')
    msg['Subject'] = t
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Successfully Published: {t}")
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
else:
    print("❌ Critical Failure: Content not generated correctly.")
