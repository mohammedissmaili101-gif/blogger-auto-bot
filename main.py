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
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = 2026

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}
Role: Expert Tech Journalist.
Task: Write a 1000-word exclusive tech report for {current_year}.
Format:
[TITLE] Title here
[KEYWORDS] words here
[META] description here
[CONTENT] HTML only, no markdown, no code blocks.
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

        # Extraction logic - Simplified to avoid regex issues
        t_part = re.search(r"\[TITLE\](.*?)\[", raw, re.S | re.I)
        k_part = re.search(r"\[KEYWORDS\](.*?)\[", raw, re.S | re.I)
        m_part = re.search(r"\[META\](.*?)\[", raw, re.S | re.I)
        c_part = re.search(r"\[CONTENT\](.*)", raw, re.S | re.I)

        title = t_part.group(1).strip() if t_part else "Global Tech News"
        keywords = k_part.group(1).strip() if k_part else "technology"
        meta = m_part.group(1).strip() if m_part else "Latest update."
        
        # التنظيف النهائي - بلا "replace" اللي كانت كدير Error
        content = ""
        if c_part:
            content = c_part.group(1).strip()
            # حيدت أي سطر فيه ``` باش نضمن الـ HTML يكون نقي
            content = "\n".join([line for line in content.splitlines() if "
```" not in line])

        return title, keywords, meta, content
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None

def get_pexels_image(kw):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(kw)}&per_page=1"
        r = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        return r.json()['photos'][0]['src']['large2x']
    except:
        return "https://picsum.photos/1200/630"

# ── Execution ─────────────────────────────────────────────
title, keywords, meta, article_body = generate_content()

if title and article_body:
    image = get_pexels_image(keywords)
    
    html_mail = f"""
    <html>
    <body style="font-family: sans-serif; max-width: 800px; margin: auto; line-height: 1.6;">
        <h1 style="color: #111;">{title}</h1>
        <p style="color: #666;">Published: {today_date}</p>
        <img src="{image}" style="width: 100%; border-radius: 10px;">
        <div style="margin-top: 20px; font-size: 18px;">
            {article_body}
        </div>
    </body>
    </html>
    """

    msg = MIMEText(html_mail, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(MY_GMAIL, GMAIL_PASS)
        server.send_message(msg)
    print("✅ Success!")
