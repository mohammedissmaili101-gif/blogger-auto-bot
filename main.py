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

# برومبت أقوى لضمان عدم خروج البوت عن النص
prompt = f"""
Current Date: {today_date}
Role: Expert Tech Journalist for Smart Flow Lab.
Task: Write a high-quality article for Google News about: {chosen_topic}

Format your response EXACTLY as follows (Don't include any conversational text):
[TITLE] (Catchy professional headline)
[KEYWORDS] (3 relevant keywords for image search)
[META] (SEO description)
[CONTENT]
(HTML body: Use <h2>, <p>, <strong>, <blockquote>. Min 1000 words.)
"""

def parse_response(raw):
    try:
        # استخراج العناوين بمرونة عالية جداً
        title_search = re.search(r"\[TITLE\]\s*(.*)", raw, re.IGNORECASE)
        kw_search = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.IGNORECASE)
        meta_search = re.search(r"\[META\]\s*(.*)", raw, re.IGNORECASE)
        
        content_parts = re.split(r"\[CONTENT\]", raw, flags=re.IGNORECASE)
        content = content_parts[-1].strip() if len(content_parts) > 1 else ""

        # تنظيف العناوين من أي رموز ماركداون
        title = title_search.group(1).strip() if title_search else chosen_topic
        title = re.sub(r'[#*]', '', title) 

        keywords = kw_search.group(1).strip() if kw_search else "tech productivity"
        meta_desc = meta_search.group(1).strip() if meta_search else "Professional productivity analysis."
        
        content = re.sub(r'```html|```', '', content).strip()
        
        return title, keywords, meta_desc, content
    except:
        return chosen_topic, "productivity", "Expert analysis", ""

def get_best_pexels_image(keywords):
    # تم تصحيح الروابط هنا (حذف الأقواس المربعة)
    fallback_img = f"https://picsum.photos/seed/{random.randint(1,999)}/1200/630"
    if not PEXELS_KEY: return fallback_img
    try:
        query = urllib.parse.quote(keywords)
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        photos = res.json().get("photos", [])
        return photos[0]["src"]["large2x"] if photos else fallback_img
    except:
        return fallback_img

def build_html(title, meta_desc, image_url, article_body):
    # تصميم متوافق مع Google News (نظيف واحترافي)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: auto; padding: 20px; background: #fff; }}
  .header {{ border-bottom: 2px solid #eee; margin-bottom: 30px; padding-bottom: 20px; }}
  h1 {{ font-size: 2.5rem; color: #111; margin-bottom: 10px; }}
  .meta-top {{ color: #666; font-size: 0.9rem; margin-bottom: 20px; }}
  .main-img {{ width: 100%; height: auto; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
  h2 {{ color: #2c3e50; margin-top: 40px; border-left: 5px solid #3498db; padding-left: 15px; }}
  p {{ margin-bottom: 20px; font-size: 1.1rem; }}
  blockquote {{ background: #f9f9f9; border-left: 10px solid #ccc; margin: 1.5em 10px; padding: 0.5em 10px; font-style: italic; }}
  .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; font-size: 0.8rem; color: #999; text-align: center; }}
</style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <div class="meta-top">Published by <strong>Smart Flow Editorial</strong> • {today_date} • 5 min read</div>
  </div>
  
  <img src="{image_url}" class="main-img" alt="{title}">
  
  <div class="article-content">
    {article_body}
  </div>

  <div class="footer">
    © {current_year} Smart Flow Lab. All rights reserved. <br>
    Indexed for Productivity Intelligence.
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
    print("🚀 Running Google News Optimized Automation...")
    t, k, m, body = None, None, None, None
    
    for _ in range(3): # محاولة التوليد حتى ينجح
        t, k, m, body = parse_response(client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            max_tokens=4000
        ).choices[0].message.content)
        if len(body) > 500: break

    if t and body:
        img_link = get_best_pexels_image(k)
        full_html = build_html(t, m, img_link, body)
        send_email(t, full_html)
        print(f"✅ Success! Published: {t}")
    else:
        print("❌ Failed to generate quality content.")
