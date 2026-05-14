import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import google.generativeai as genai
from email.mime.text import MIMEText

# ── Secrets (تبديل GROQ بـ GEMINI) ──────────────────────
GEMINI_KEY   = os.environ.get("GEMINI_API_KEY")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

# إعداد Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = 2026

# ── Topic Rotation System ─────────────────────────────────
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year}",
    f"a BREAKTHROUGH scientific study published in {current_year} about productivity",
    f"a revolutionary AI-powered tool for students in {current_year}",
    f"a major SILICON VALLEY corporate shakeup happening RIGHT NOW in {current_year}",
    f"the battle between OpenAI vs Google vs Meta in {current_year}",
]

random_modifier = random.choice([
    "Focus on a hidden scandal.",
    "Write from an insider leak perspective.",
    "Highlight extreme financial implications.",
    "Use a high-stakes thriller headline."
])

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt (بقينا على نفس الستيل ديالك) ──────────────────
prompt = f"""
Current Date: {today_date}
Angle: {random_modifier}
Story: {chosen_topic}

Write an investigative article (Minimum 1100 words for Google Ads SEO). 
Structure MUST use tags: [TITLE], [KEYWORDS], [META], [CONTENT].
Inside [CONTENT], use ONLY HTML tags like <p>, <h2>, <h3>, <strong>, <em>.
Be very detailed, invent specific names, and use a professional journalist tone.
"""

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    # تنظيف الماركداون إذا وجد
    clean_raw = raw.replace('**', '').replace('#', '')
    
    title = re.search(r"\[TITLE\]\s*(.*)", clean_raw, re.IGNORECASE)
    kw = re.search(r"\[KEYWORDS\]\s*(.*)", clean_raw, re.IGNORECASE)
    meta = re.search(r"\[META\]\s*(.*)", clean_raw, re.IGNORECASE)
    content = re.search(r"\[CONTENT\]\s*(.*)", raw, re.DOTALL | re.IGNORECASE)

    res_title = title.group(1).split('[')[0].strip() if title else f"Tech Insights {today_date}"
    res_kw = kw.group(1).split('[')[0].strip() if kw else "tech, innovation"
    res_meta = meta.group(1).split('[')[0].strip()[:160] if meta else "Exclusive deep-dive."
    
    if content:
        res_content = content.group(1).strip()
    else:
        res_content = raw.split('[CONTENT]')[-1] if '[CONTENT]' in raw else raw

    res_content = re.sub(r'```.*?```', '', res_content, flags=re.DOTALL)
    return res_title[:65], res_kw, res_meta, res_content

# ── Content Generation (Gemini Edition) ──────────────────
def generate_content():
    try:
        response = model.generate_content(prompt)
        if response.text:
            return parse_response(response.text)
        return None, None, None, None
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None, None, None, None

# ── Pexels Image ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    headers = {"Authorization": PEXELS_KEY}
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1"
        res = requests.get(url, headers=headers, timeout=15).json()
        return res["photos"][0]["src"]["large2x"] if res.get("photos") else "https://picsum.photos/1200/630"
    except:
        return "https://picsum.photos/1200/630"

# ── Final Main Function ───────────────────────────────────
def main():
    print("🚀 Starting Gemini-Powered Blogger Bot...")
    title, keywords, meta, content = generate_content()
    
    if title and len(content) > 800:
        image_url = get_best_pexels_image(keywords)
        
        full_html = f"""
        <div dir="ltr" style="font-family: 'Segoe UI', Tahoma, sans-serif; line-height: 1.8; color: #1a1a1a; max-width: 800px; margin: auto;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="{image_url}" style="width: 100%; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);" alt="{title}">
            </div>
            <div style="text-align: justify; font-size: 19px;">
                {content}
            </div>
            <hr style="margin-top: 50px; border: 0; border-top: 1px solid #eee;">
            <p style="text-align: center; color: #888; font-size: 13px;">
                © {current_year} Smart Flow Lab Intelligence. All Rights Reserved.
            </p>
        </div>
        """
        
        msg = MIMEText(full_html, 'html', 'utf-8')
        msg['Subject'] = title
        msg['From'] = MY_GMAIL
        msg['To'] = BLOGGER_MAIL
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(MY_GMAIL, GMAIL_PASS)
                server.send_message(msg)
            print(f"✅ Published: {title}")
        except Exception as e:
            print(f"❌ Email Error: {e}")
    else:
        print("❌ Script stopped: Content too short or Generation failed.")

if __name__ == "__main__":
    main()
