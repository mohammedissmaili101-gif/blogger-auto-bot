import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import time
from email.mime.text import MIMEText

# ── Secrets ───────────────────────────────────────────────
HF_TOKEN     = os.environ.get("HF_TOKEN")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = 2026

# ── Topic Rotation System ─────────────────────────────────
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year}",
    f"a BREAKTHROUGH scientific study about productivity in {current_year}",
    f"a revolutionary AI tool for students in {current_year}",
    f"the battle between OpenAI vs Google vs Meta in {current_year}",
]

random_modifier = random.choice([
    "Focus on a hidden scandal or controversy.",
    "Highlight the extreme financial implications.",
    "Make the title sound like a high-stakes thriller headline."
])

chosen_topic = random.choice(TOPIC_ANGLES)

# ── HF Inference Client (API الجديد) ─────────────────────
def call_hf_api(user_prompt):
    # ✅ API الجديد ديال HF - يشتغل مع كل الموديلات
    API_URL = "https://api-inference.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "max_tokens": 2500,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False
    }

    for attempt in range(1, 4):
        try:
            print(f"🤖 Attempt {attempt}/3...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]

            elif response.status_code == 503:
                print("⏳ Model loading, waiting 30s...")
                time.sleep(30)
                continue

            else:
                print(f"❌ HF Error {response.status_code}: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"❌ Request Error: {e}")
            time.sleep(10)

    return None

# ── Prompt ────────────────────────────────────────────────
def build_prompt():
    return f"""Current Date: {today_date}
Angle: {random_modifier}
Story: {chosen_topic}

You are an investigative tech journalist. Write a detailed article (minimum 1000 words).

IMPORTANT - Start your response with exactly this structure:
[TITLE] your title here (under 65 chars, specific and punchy)
[KEYWORDS] keyword1, keyword2, keyword3
[META] your meta description here (under 160 chars)
[CONTENT]
your full article here using only HTML tags: <p>, <h2>, <h3>, <strong>, <em>, <blockquote>

Rules:
- No markdown, no asterisks, no hashtags
- Minimum 1000 words in the article body
- Make the title unique and specific to this story
- Focus on technical depth and exclusive analysis"""

# ── Robust Parser ─────────────────────────────────────────
def parse_response(raw):
    if not raw:
        return None, None, None, None

    raw_clean = re.sub(r'[*#]', '', raw)

    title_match   = re.search(r"\[TITLE\]\s*(.*)",   raw_clean, re.IGNORECASE)
    kw_match      = re.search(r"\[KEYWORDS\]\s*(.*)", raw_clean, re.IGNORECASE)
    meta_match    = re.search(r"\[META\]\s*(.*)",     raw_clean, re.IGNORECASE)
    content_match = re.search(r"\[CONTENT\]\s*(.*)",  raw_clean, re.DOTALL | re.IGNORECASE)

    title     = title_match.group(1).split('[')[0].strip()        if title_match   else f"Tech Exclusive {today_date}"
    keywords  = kw_match.group(1).split('[')[0].strip()           if kw_match      else "tech, ai, innovation"
    meta_desc = meta_match.group(1).split('[')[0].strip()[:160]   if meta_match    else "Deep dive analysis."

    if content_match:
        content = content_match.group(1).strip()
    else:
        html_start = re.search(r"(<p>|<h2>).*", raw_clean, re.DOTALL | re.IGNORECASE)
        content = html_start.group(0) if html_start else raw_clean

    return title[:65], keywords, meta_desc, content

# ── Content Generation ────────────────────────────────────
def generate_content():
    prompt = build_prompt()
    raw = call_hf_api(prompt)

    if not raw:
        print("❌ No response from HF API.")
        return None, None, None, None

    return parse_response(raw)

# ── Pexels Image ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY:
        return "https://picsum.photos/1200/630"
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        return res["photos"][0]["src"]["large2x"] if res.get("photos") else "https://picsum.photos/1200/630"
    except:
        return "https://picsum.photos/1200/630"

# ── Main ──────────────────────────────────────────────────
def main():
    print("🚀 Starting HF-Powered Bot...")
    print(f"📌 Topic: {chosen_topic[:80]}")
    print(f"🎯 Angle: {random_modifier}")

    title, keywords, meta, content = generate_content()

    if title and content and len(content) > 600:
        print(f"📰 Title: {title}")
        img = get_best_pexels_image(keywords)

        html = f"""
        <div dir="ltr" style="font-family: Arial; line-height: 1.8; font-size: 18px; color: #333;">
            <img src="{img}" style="width: 100%; border-radius: 8px;" alt="{title}">
            <div style="margin-top: 20px;">{content}</div>
        </div>
        """

        msg = MIMEText(html, 'html', 'utf-8')
        msg['Subject'] = title
        msg['From']    = MY_GMAIL
        msg['To']      = BLOGGER_MAIL

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(MY_GMAIL, GMAIL_PASS)
                server.send_message(msg)
            print(f"✅ Published to Blogger: {title}")
        except Exception as e:
            print(f"❌ Email Error: {e}")
    else:
        print("❌ Generation failed or content too short.")

if __name__ == "__main__":
    main()
