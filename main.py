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

# ── Smart Flow Productivity Topics (مواضيع الإنتاجية الذكية) ──
TOPIC_ANGLES = [
    "The 'Flow-State' Hack: How new AI agents are automating 90% of deep-work admin tasks in 2026",
    "Beyond ChatGPT: The rise of 'Autonomous Productivity OS' for seamless workflow management",
    "Micro-SaaS Productivity: How to build a $10k/month automated business using only 3 AI tools",
    "The Death of the Search Bar: Why AI-Integrated Browsers are the ultimate research weapon",
    "AI-Driven Time Boxing: Why traditional To-Do lists are obsolete and the 'Smart Flow' alternative",
    "The 4-Hour Work Week 2.0: Using AI Automation to replace manual data entry forever",
    "Personal Knowledge Management (PKM): Building a digital second brain that actually thinks",
    "The Productivity Crisis: How to consolidate too many AI tools into one unified workflow",
    "Voice-to-Action: Turning messy 2026 voice notes into full project plans in seconds",
    "The Ultimate AI Stack for Solopreneurs: 5 tools to run a high-scale digital business alone"
]

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Updated Professional Prompt ───────────────────────────
prompt = f"""
Current Date: {today_date}
You are a world-class productivity expert and tech consultant for 'Smart Flow Lab'. 
Your style is clear, actionable, professional, and data-driven.

YOUR TASK: 
Write an EXCLUSIVE deep-dive analysis on: {chosen_topic}

CRITICAL STRUCTURE:
[TITLE] (Actionable, curiosity gap headline, under 60 chars, no quotes)
[KEYWORDS] (3 visual keywords for image search)
[META] (150-char SEO description)
[CONTENT]
(Write a 1000+ word HTML article. Use <h2> for subheadings, <p> for text, <strong> for emphasis, and <blockquote> for expert insights. DO NOT use markdown code fences like ```)
"""

# ── Robust Parser (إصلاح شامل لمنطق استخراج النصوص) ──────────
def parse_response(raw):
    try:
        # استخراج الأجزاء باستخدام Regex مرن
        title_match = re.search(r"\[TITLE\]\s*(.*)", raw, re.IGNORECASE)
        kw_match    = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.IGNORECASE)
        meta_match  = re.search(r"\[META\]\s*(.*)", raw, re.IGNORECASE)
        
        # استخراج المحتوى (كل ما بعد [CONTENT])
        content_parts = re.split(r"\[CONTENT\]", raw, flags=re.IGNORECASE)
        content = content_parts[1].strip() if len(content_parts) > 1 else ""

        # تنظيف العناوين والكلمات المفتاحية من أي زوائد
        title = title_match.group(1).split("[")[0].strip() if title_match else "Smart Productivity Update"
        title = re.sub(r'[#*`"]', '', title)

        keywords = kw_match.group(1).split("[")[0].strip() if kw_match else "productivity AI automation"
        meta_desc = meta_match.group(1).split("[")[0].strip()[:160] if meta_match else "Master your workflow with Smart Flow Lab."

        # تنظيف المحتوى من أي محاولة للبوت لاستخدام Markdown
        content = re.sub(r'```html|```', '', content).strip()
        
        return title, keywords, meta_desc, content
    except Exception as e:
        print(f"⚠️ Parsing error details: {e}")
        return None, None, None, None

# ── Content Generation ───────────────────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7, # خفضنا الحرارة شوية باش يكون الأسلوب مهني أكثر
                max_tokens=4000,
            )
            raw = completion.choices[0].message.content
            t, k, m, c = parse_response(raw)
            # التأكد من أن المقال طويل بما يكفي قبل الموافقة
            if t and c and len(c) > 800: return t, k, m, c
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
    return None, None, None, None

# ── Image Fetching ───────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return f"[https://picsum.photos/seed/](https://picsum.photos/seed/){random.randint(1,999)}/1200/628"
    try:
        url = f"[https://api.pexels.com/v1/search?query=](https://api.pexels.com/v1/search?query=){urllib.parse.quote(keywords)}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        photos = res.json().get("photos", [])
        return photos[0]["src"]["large2x"] if photos else "[https://picsum.photos/1200/628](https://picsum.photos/1200/628)"
    except:
        return "[https://picsum.photos/1200/628](https://picsum.photos/1200/628)"

# ── Magazine Style HTML ──────────────────────────────────
def build_html(title, meta_desc, image_url, article_body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="description" content="{meta_desc}">
<style>
  body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #f4f7f6; color: #2c3e50; line-height: 1.8; margin: 0; }}
  .container {{ max-width: 800px; margin: 50px auto; padding: 40px; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-radius: 8px; }}
  .brand {{ color: #3498db; font-weight: bold; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; }}
  h1 {{ font-size: 38px; color: #1a1a1a; margin: 10px 0 20px 0; line-height: 1.2; }}
  .meta {{ font-size: 13px; color: #95a5a6; border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
  img {{ width: 100%; border-radius: 6px; margin-bottom: 30px; }}
  h2 {{ color: #2980b9; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 15px; }}
  blockquote {{ background: #f9f9f9; border-left: 6px solid #3498db; margin: 30px 0; padding: 20px; font-style: italic; font-size: 18px; }}
  footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #bdc3c7; }}
</style>
</head>
<body>
<div class="container">
  <div class="brand">Smart Flow Lab | Productivity Intelligence</div>
  <h1>{title}</h1>
  <div class="meta">By Smart Flow Editorial • {today_date} • 2026 Edition</div>
  <img src="{image_url}" alt="Productivity Workflow">
  <div class="content">{article_body}</div>
  <footer>© {current_year} Smart Flow Lab. Actionable AI Insights.</footer>
</div>
</body>
</html>"""

# ── Email System ─────────────────────────────────────────
def send_email(title, html_body):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(MY_GMAIL, GMAIL_PASS)
        server.send_message(msg)

# ── Main Execution ───────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Smart Flow Lab Automation...")
    t, k, m, body = generate_content()
    if t and body:
        img = get_best_pexels_image(k)
        html = build_html(t, m, img, body)
        send_email(t, html)
        print(f"✅ Post Published Successfully: {t}")
    else:
        print("❌ Failed to generate actionable content.")
