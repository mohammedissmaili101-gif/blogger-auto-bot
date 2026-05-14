import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import time
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

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}
Angle: {random_modifier}
Story: {chosen_topic}

Write an investigative article (Around 800-900 words to avoid rate limits). 
Structure MUST use tags: [TITLE], [KEYWORDS], [META], [CONTENT].
Inside [CONTENT], use ONLY HTML: <p>, <h2>, <strong>, <em>.
"""

# ── Robust Parser (FIXED FOR GITHUB ACTIONS) ─────────────
def parse_response(raw):
    # مسح الرموز اللي كتدير مشاكل فـ Python String
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
        # Fallback if parser fails
        res_content = raw.split('[CONTENT]')[-1] if '[CONTENT]' in raw else raw

    # Clean Markdown leftovers
    res_content = re.sub(r'```.*?```', '', res_content, flags=re.DOTALL)
    return res_title[:65], res_kw, res_meta, res_content

# ── Content Generation (WITH RATE LIMIT HANDLING) ────────
def generate_content():
    try:
        # الموديل الأنسب حاليا لتفادي الايرور 429
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.8,
            max_tokens=3000, # نقصناه شوية باش مايتبلوكاش الحساب المجاني
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
        res = requests.get(url, headers=headers, timeout=15).json()
        return res["photos"][0]["src"]["large2x"] if res.get("photos") else "https://picsum.photos/1200/630"
    except:
        return "https://picsum.photos/1200/630"

# ── Final Main Function ───────────────────────────────────
def main():
    print("🚀 Starting Professional Blogger Bot...")
    title, keywords, meta, content = generate_content()
    
    if title and len(content) > 500:
        image_url = get_best_pexels_image(keywords)
        
        # Build HTML
        full_html = f"""
        <div dir="ltr" style="font-family: 'Segoe UI', Tahoma, sans-serif; line-height: 1.7; color: #222;">
            <img src="{image_url}" style="width: 100%; border-radius: 12px; margin-bottom: 20px;" alt="{title}">
            <div style="text-align: justify;">{content}</div>
            <p style="margin-top: 50px; border-top: 1px solid #eee; padding-top: 10px; font-size: 12px; color: #777;">
                Published automatically by Smart Flow Lab Intelligence © {current_year}
            </p>
        </div>
        """
        
        # Send Email
        msg = MIMEText(full_html, 'html', 'utf-8')
        msg['Subject'] = title
        msg['From'] = MY_GMAIL
        msg['To'] = BLOGGER_MAIL
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(MY_GMAIL, GMAIL_PASS)
                server.send_message(msg)
            print(f"✅ Published Successfully: {title}")
        except Exception as e:
            print(f"❌ Email Error: {e}")
    else:
        print("❌ Script stopped: Content generation failed or was blocked by Rate Limits.")

if __name__ == "__main__":
    main()
