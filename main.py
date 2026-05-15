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
GROQ_KEY     = os.environ.get("GROQ_API_KEY", "")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD", "")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL", "")
MY_GMAIL     = os.environ.get("MY_GMAIL", "")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY", "")

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %Y")

# ── Topic Rotation ──
TOPIC_ANGLES = ["AI Trends 2026", "Tech Innovation", "Future of Work", "Digital Transformation"]
chosen_topic = random.choice(TOPIC_ANGLES)

def groq_call(prompt, tokens=1500):
    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return None

def main():
    print("🚀 Starting Smart Flow Lab...")
    
    # 1. Metadata Generation
    meta_prompt = f"Topic: {chosen_topic}. Generate exactly: [TITLE] title here, [KEYWORDS] keywords here"
    meta_raw = groq_call(meta_prompt, 200)
    
    if not meta_raw: 
        print("❌ Groq didn't respond."); return

    # نظام حماية في حالة مالقاش [TITLE]
    title_match = re.search(r"\[TITLE\]\s*(.*)", meta_raw, re.I)
    title = title_match.group(1).strip() if title_match else f"Tech Update: {chosen_topic}"
    title = re.sub(r'[#*`]', '', title) # تنظيف العنوان

    # 2. Content Generation
    art_prompt = f"Write a professional 800-word article for: {title}. Use HTML <p> and <h2> only."
    content = groq_call(art_prompt, 1800)
    if not content: return

    # 3. Image (استعمال Picsum لتفادي أخطاء Pexels حالياً)
    img = "https://picsum.photos/1200/630"

    # 4. بناء الإيميل بطريقة MIMEMultipart (الأضمن لـ Blogger)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = title
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL

    html_body = f"""
    <html>
      <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: auto; padding: 20px; border: 1px solid #eee;">
          <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{title}</h1>
          <img src="{img}" style="width:100%; border-radius: 8px; margin: 20px 0;">
          <div style="font-size: 18px; color: #444;">{content}</div>
          <hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0;">
          <p style="text-align: center; color: #999; font-size: 12px;">© 2026 Smart Flow Lab Intelligence Engine</p>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        # استعمال SMTP مع starttls أضمن في GitHub Actions لتفادي أخطاء الـ bytes
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ SUCCESS: {title}")
    except Exception as e:
        print(f"❌ Email Error: {e}")

if __name__ == "__main__":
    main()
