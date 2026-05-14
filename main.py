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

prompt = f"""
Current Date: {today_date}
You are a world-class productivity expert for 'Smart Flow Lab'. 

TASK: Write an EXCLUSIVE deep-dive analysis on: {chosen_topic}

STRICT FORMAT:
[TITLE] Put Title Here
[KEYWORDS] word1, word2, word3
[META] Put 150 char description here
[CONTENT]
Write a 1000+ word HTML article. Use <h2>, <p>, <strong>, <blockquote>.
Do NOT use markdown code blocks like ```html.
"""

# ── Improved Parser ──────────────────────────────────────
def parse_response(raw):
    try:
        # البحث عن الأنماط بشكل أكثر مرونة (يدعم وجود أو عدم وجود الأقواس)
        title = re.search(r"\[?TITLE\]?[:\s]*(.*)", raw, re.IGNORECASE)
        keywords = re.search(r"\[?KEYWORDS\]?[:\s]*(.*)", raw, re.IGNORECASE)
        meta = re.search(r"\[?META\]?[:\s]*(.*)", raw, re.IGNORECASE)
        
        # استخراج المحتوى: كل شيء بعد كلمة CONTENT
        content_match = re.split(r"\[?CONTENT\]?", raw, flags=re.IGNORECASE)
        content = content_match[-1].strip() if len(content_match) > 1 else ""

        # تنظيف النتائج
        final_title = title.group(1).strip() if title else "Productivity Insights " + today_date
        final_keywords = keywords.group(1).strip() if keywords else "productivity, ai, tech"
        final_meta = meta.group(1).strip()[:160] if meta else "Latest productivity update from Smart Flow Lab."
        
        # إزالة أي علامات ماركداون متبقية
        content = re.sub(r'```html|```', '', content).strip()
        
        return final_title, final_keywords, final_meta, content
    except Exception as e:
        print(f"⚠️ Parsing error: {e}")
        return None, None, None, None

# ── Content Generation ───────────────────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=4000,
            )
            raw = completion.choices[0].message.content
            t, k, m, c = parse_response(raw)
            
            # تم تقليل الحد لـ 500 حرف لضمان المرونة
            if t and c and len(c) > 500: 
                return t, k, m, c
            else:
                print(f"⚠️ Attempt {attempt}: Content too short or parsing failed. Length: {len(c) if c else 0}")
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
    return None, None, None, None

# ── Image Fetching ───────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return "[https://picsum.photos/1200/628](https://picsum.photos/1200/628)"
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
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; color: #2c3e50; line-height: 1.8; margin: 0; }}
  .container {{ max-width: 800px; margin: 50px auto; padding: 40px; background: #fff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
  h1 {{ font-size: 32px; color: #1a1a1a; margin-bottom: 20px; }}
  img {{ width: 100%; border-radius: 6px; margin-bottom: 30px; }}
  h2 {{ color: #2980b9; margin-top: 30px; }}
  blockquote {{ background: #f9f9f9; border-left: 5px solid #3498db; padding: 15px; font-style: italic; }}
  footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #bdc3c7; }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <p><em>{meta_desc}</em></p>
  <img src="{image_url}" alt="Article Hero Image">
  <div class="content">{article_body}</div>
  <footer>© {current_year} Smart Flow Lab.</footer>
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
        print("❌ Critical Failure: Could not generate or parse content after retries.")
