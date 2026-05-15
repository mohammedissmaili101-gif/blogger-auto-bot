import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from groq import Groq

# ── Secrets ───────────────────────────────────────────────
GROQ_KEY     = os.environ.get("GROQ_API_KEY")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %Y")

# ── Topic Rotation ──
TOPIC_ANGLES = [
    "AI breakthroughs in 2026", "Future of Robotics", 
    "OpenAI vs Google battle", "AI in medical science"
]
chosen_topic = random.choice(TOPIC_ANGLES)

def groq_call(prompt, tokens=1500):
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=tokens,
        )
        return completion.choices[0].message.content
    except: return None

def main():
    print("🚀 Starting Smart Flow Lab...")
    
    # 1. Generate Metadata
    meta_prompt = f"Topic: {chosen_topic}. Generate: [TITLE], [KEYWORDS], [META]"
    meta_raw = groq_call(meta_prompt, 200)
    if not meta_raw: return
    
    title = re.search(r"\[TITLE\](.*)", meta_raw, re.I).group(1).strip()
    
    # 2. Generate Article
    art_prompt = f"Write 800 words article for title: {title}. Use HTML <p>, <h2>. No markdown."
    content = groq_call(art_prompt, 1500)
    if not content: return

    # 3. Image
    img = f"https://picsum.photos/1200/630" # سريع ومضمون

    # 4. بناء هيكل الإيميل الاحترافي (هذا هو السر)
    # استعملنا MIMEMultipart باش بلوجر يقرأ العنوان والمحتوى بشكل صحيح
    msg = MIMEMultipart('alternative')
    msg['Subject'] = title
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL

    html_body = f"""
    <html>
      <head></head>
      <body style="font-family: Arial; font-size: 16px;">
        <h1 style="color: #2c3e50;">{title}</h1>
        <img src="{img}" style="width:100%; border-radius:10px;">
        <div style="margin-top:20px;">{content}</div>
        <p style="color: grey; font-size: 12px;">Published by Smart Flow Lab Engine</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ DONE! Published: {title}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
