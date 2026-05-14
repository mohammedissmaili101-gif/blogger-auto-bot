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

# ── Topic Rotation System ─────────────────────────────────
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year}",
    f"a BREAKTHROUGH scientific study published in {current_year} about cognition",
    f"a revolutionary AI-powered tool for researchers in {current_year}",
    f"a major SILICON VALLEY corporate shakeup happening RIGHT NOW in {current_year}",
    f"cutting-edge AI application in healthcare or climate tech in {current_year}",
    f"the battle between OpenAI vs Google vs Meta in {current_year}",
    f"how a new AI coding tool in {current_year} is transforming engineering",
    f"a viral AI use case regular people are adopting in {current_year}",
]

random_modifier = random.choice([
    "Focus on a hidden scandal or controversy.",
    "Write it from the perspective of an insider leak.",
    "Highlight the extreme financial implications.",
    "Focus on a specific technical term.",
    "Make the title sound like a high-stakes thriller headline."
])

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}
Angle: {random_modifier}
Story: {chosen_topic}

Write an investigative article (Min 1000 words). 
Structure: [TITLE], [KEYWORDS], [META], [CONTENT] (using only HTML tags like <p>, <h2>, <strong>).
"""

# ── Robust Parser (FIXED SYNTAX ERROR) ───────────────────
def parse_response(raw):
    # تنظيف بدائي للرموز اللي كدير مشاكل
    raw_clean = raw.replace('**', '').replace('#', '')
    
    title_match = re.search(r"\[TITLE\]\s*(.*)", raw_clean, re.IGNORECASE)
    kw_match    = re.search(r"\[KEYWORDS\]\s*(.*)", raw_clean, re.IGNORECASE)
    meta_match  = re.search(r"\[META\]\s*(.*)", raw_clean, re.IGNORECASE)
    content_match = re.search(r"\[CONTENT\]\s*(.*)", raw, re.DOTALL | re.IGNORECASE)

    title = title_match.group(1).split('[')[0].strip() if title_match else f"Tech Update {today_date}"
    title = re.sub(r'[^\w\s\-]', '', title)[:65]
    
    keywords = kw_match.group(1).split('[')[0].strip() if kw_match else "tech, ai"
    meta_desc = meta_match.group(1).split('[')[0].strip()[:160] if meta_match else "Deep dive analysis."

    if content_match:
        content = content_match.group(1).strip()
    else:
        # البحث عن أول وسم HTML إذا فشل الـ Parser
        html_start = re.search(r"(<p>|<h2>).*", raw, re.DOTALL | re.IGNORECASE)
        content = html_start.group(0) if html_start else raw

    # تنظيف كود الماركداون بـ regex آمن
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    return title, keywords, meta_desc, content

# ── Content Generation ────────────────────────────────────
def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            # الموديل المحدث والمتاح حالياً
            model="llama-3.3-70b-versatile", 
            temperature=0.8,
            max_tokens=3500,
        )
        return parse_response(completion.choices[0].message.content)
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return None, None, None, None

# ── Pexels Image ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    headers = {"Authorization": PEXELS_KEY}
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1"
        res = requests.get(url, headers=headers, timeout=10).json()
        return res["photos"][0]["src"]["large2x"] if res.get("photos") else "https://picsum.photos/1200/630"
    except:
        return "https://picsum.photos/1200/630"

# ── HTML & Email ──────────────────────────────────────────
def build_html(title, image_url, article_body):
    return f"""
    <div dir="ltr" style="font-family: Georgia, serif; line-height: 1.8; font-size: 19px; max-width: 800px; margin: auto; padding: 20px; color: #333;">
        <img src="{image_url}" style="width: 100%; border-radius: 8px; margin-bottom: 25px;" alt="{title}">
        <div class="content">{article_body}</div>
        <p style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 10px; color: #999; font-size: 14px;">
            Published via Smart Flow Lab | {today_date}
        </p>
    </div>
    """

def send_email(title, html_body):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title.strip()
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=60) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published: {title}")
    except Exception as e:
        print(f"❌ SMTP Error: {e}")

def main():
    print("🚀 Bot starting...")
    title, keywords, meta, content = generate_content()
    
    # التأكد من أن المقال طويل كفاية (لـ Google Ads)
    if title and len(content) > 600:
        img = get_best_pexels_image(keywords)
        html = build_html(title, img, content)
        send_email(title, html)
    else:
        print("❌ Generation failed or too short.")

if __name__ == "__main__":
    main()
