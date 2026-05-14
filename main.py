import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
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
current_year = datetime.date.today().year

TOPIC_ANGLES = [
    "The 'Flow-State' Hack: How AI agents automate deep-work in 2026",
    "Beyond ChatGPT: The rise of Autonomous Productivity OS",
    "Micro-SaaS Productivity: Build a $10k/month business with AI",
    "The Death of Search: Why AI-Integrated Browsers are the future",
    "AI-Driven Time Boxing: Why traditional To-Do lists are obsolete",
    "The 4-Hour Work Week 2.0: Replacing manual data entry with AI",
    "Personal Knowledge Management: Building a digital second brain",
    "The Productivity Crisis: Consolidating AI tools into one workflow",
    "Voice-to-Action: Turning messy voice notes into project plans",
    "The Ultimate AI Stack for Solopreneurs in 2026"
]

chosen_topic = random.choice(TOPIC_ANGLES)

prompt = f"""
Current Date: {today_date}
Role: Senior Tech Journalist for Smart Flow Lab.
Task: Write a deep-dive technical article (1000+ words) about: {chosen_topic}

Required Structure (STRICT):
[TITLE] Headline
[KEYWORDS] search terms
[META] short description
[CONTENT]
Full HTML body with <h2>, <p>, <strong>. No markdown blocks.
"""

def parse_response(raw):
    """نظام تحليل مرن جداً لتجنب الفشل"""
    try:
        # استخراج الأجزاء مع مراعاة وجود Markdown (مثل **[TITLE]**)
        title = re.search(r"TITLE\]?[:\s]*(.*)", raw, re.IGNORECASE)
        keywords = re.search(r"KEYWORDS\]?[:\s]*(.*)", raw, re.IGNORECASE)
        meta = re.search(r"META\]?[:\s]*(.*)", raw, re.IGNORECASE)
        
        # تقسيم المحتوى بذكاء
        content_split = re.split(r"CONTENT\]?", raw, flags=re.IGNORECASE)
        content = content_split[-1].strip() if len(content_split) > 1 else raw

        # تنظيف العناوين
        clean_title = re.sub(r'[#*\[\]]', '', title.group(1)).strip() if title else chosen_topic
        clean_kw = re.sub(r'[#*\[\]]', '', keywords.group(1)).strip() if keywords else "productivity AI"
        clean_meta = meta.group(1).strip() if meta else "Smart Flow Lab Deep Dive."
        
        # إزالة أي أكواد ماركداون (```html) قد يضيفها البوت
        content = re.sub(r'```[a-z]*', '', content).replace('```', '').strip()
        
        return clean_title, clean_kw, clean_meta, content
    except Exception as e:
        print(f"⚠️ Parsing recovery mode: {e}")
        return chosen_topic, "productivity", "AI tech update", raw

def get_best_pexels_image(keywords):
    fallback = f"[https://picsum.photos/seed/](https://picsum.photos/seed/){random.randint(1,999)}/1200/630"
    if not PEXELS_KEY: return fallback
    try:
        query = urllib.parse.quote(keywords)
        res = requests.get(f"[https://api.pexels.com/v1/search?query=](https://api.pexels.com/v1/search?query=){query}&per_page=1", 
                          headers={"Authorization": PEXELS_KEY}, timeout=10)
        data = res.json()
        return data["photos"][0]["src"]["large2x"] if data.get("photos") else fallback
    except:
        return fallback

def build_html(title, meta_desc, image_url, article_body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.8; color: #1a1a1a; max-width: 850px; margin: auto; padding: 30px; background: #fefefe; }}
  .header {{ text-align: center; border-bottom: 3px solid #3498db; margin-bottom: 40px; padding-bottom: 20px; }}
  h1 {{ font-size: 42px; margin-bottom: 10px; color: #2c3e50; line-height: 1.2; }}
  .meta-info {{ color: #7f8c8d; font-style: italic; margin-bottom: 20px; }}
  .hero-img {{ width: 100%; border-radius: 12px; margin-bottom: 35px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
  h2 {{ color: #2980b9; margin-top: 45px; font-size: 28px; border-left: 6px solid #3498db; padding-left: 15px; }}
  p {{ margin-bottom: 25px; font-size: 19px; }}
  blockquote {{ background: #f8f9fa; border-left: 8px solid #bdc3c7; padding: 20px; margin: 30px 0; font-style: italic; font-size: 21px; }}
  .footer {{ margin-top: 60px; padding: 30px; background: #2c3e50; color: white; border-radius: 8px; text-align: center; }}
</style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <div class="meta-info">By Smart Flow Editorial Team • Updated {today_date}</div>
  </div>
  <img src="{image_url}" class="hero-img" alt="Productivity Trends">
  <div class="main-content">
    {article_body}
  </div>
  <div class="footer">
    © {current_year} Smart Flow Lab. Empowering workflows through AI.
  </div>
</body>
</html>"""

def send_email(title, html_body):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(MY_GMAIL, GMAIL_PASS)
        server.send_message(msg)

if __name__ == "__main__":
    print("🚀 Smart Flow Automation Started...")
    try:
        # محاولة التوليد
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=4000
        )
        raw_text = response.choices[0].message.content
        
        # التحليل
        t, k, m, body = parse_response(raw_text)
        
        # التأكد من وجود محتوى حتى لو فشل الـ parser
        if len(body) < 100:
            raise ValueError("Content too short, AI lazy response.")

        img = get_best_pexels_image(k)
        html = build_html(t, m, img, body)
        send_email(t, html)
        print(f"✅ Success! Published: {t}")
        
    except Exception as e:
        print(f"❌ Final Critical Error: {e}")
