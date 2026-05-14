import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import time
from email.mime.text import MIMEText

# ── Secrets ──────────────────────────────────────────────
HF_TOKEN     = os.environ.get("HF_TOKEN")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

# التعديل هنا: استهداف موديل Mistral المفتوح للجميع
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

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

# ── Prompt (معدل ليتناسب مع Mistral) ─────────────────────
prompt = f"<s>[INST] Current Date: {today_date}\nAngle: {random_modifier}\nStory: {chosen_topic}\n\nWrite an investigative article (Min 1000 words). \nStructure: [TITLE], [KEYWORDS], [META], [CONTENT] (using only HTML tags like <p>, <h2>, <strong>). Focus on technical depth and exclusive leaks. [/INST]"

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    # تنظيف الماركداون
    raw_clean = re.sub(r'[*#]', '', raw)
    
    title_match = re.search(r"\[TITLE\]\s*(.*)", raw_clean, re.IGNORECASE)
    kw_match    = re.search(r"\[KEYWORDS\]\s*(.*)", raw_clean, re.IGNORECASE)
    meta_match  = re.search(r"\[META\]\s*(.*)", raw_clean, re.IGNORECASE)
    content_match = re.search(r"\[CONTENT\]\s*(.*)", raw_clean, re.DOTALL | re.IGNORECASE)

    title = title_match.group(1).split('[')[0].strip() if title_match else f"Tech Update {today_date}"
    keywords = kw_match.group(1).split('[')[0].strip() if kw_match else "tech, ai"
    meta_desc = meta_match.group(1).split('[')[0].strip()[:160] if meta_match else "Deep dive analysis."

    if content_match:
        content = content_match.group(1).strip()
    else:
        html_start = re.search(r"(<p>|<h2>).*", raw_clean, re.DOTALL | re.IGNORECASE)
        content = html_start.group(0) if html_start else raw_clean

    return title[:65], keywords, meta_desc, content

# ── Content Generation (Mistral) ──────────────────────────
def generate_content():
    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 2000,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            raw_text = result[0]['generated_text'] if isinstance(result, list) else result['generated_text']
            return parse_response(raw_text)
        elif response.status_code == 503:
            print("⏳ Mistral is loading... waiting 20s")
            time.sleep(20)
            return generate_content()
        else:
            print(f"❌ HF Error: {response.status_code} - {response.text}")
            return None, None, None, None
    except Exception as e:
        print(f"❌ Generation Error: {e}")
        return None, None, None, None

# ── Pexels & Email ────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        return res["photos"][0]["src"]["large2x"] if res.get("photos") else "https://picsum.photos/1200/630"
    except: return "https://picsum.photos/1200/630"

def main():
    print("🚀 Starting Mistral-Powered Bot (No waiting for Meta approval)...")
    title, keywords, meta, content = generate_content()
    
    if title and len(content) > 500:
        img = get_best_pexels_image(keywords)
        html = f"""
        <div dir="ltr" style="font-family: 'Segoe UI', Arial; line-height: 1.8; font-size: 18px; color: #1a1a1a;">
            <img src="{img}" style="width: 100%; border-radius: 8px; margin-bottom: 20px;" alt="{title}">
            {content}
            <p style="margin-top: 30px; color: #888; font-size: 12px; text-align: center;">© 2026 Smart Flow Lab. All Rights Reserved.</p>
        </div>
        """
        msg = MIMEText(html, 'html', 'utf-8')
        msg['Subject'] = title
        msg['From'] = MY_GMAIL
        msg['To'] = BLOGGER_MAIL
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(MY_GMAIL, GMAIL_PASS)
                server.send_message(msg)
            print(f"✅ Published: {title}")
        except Exception as e: print(f"❌ Email Error: {e}")
    else:
        print("❌ Generation failed or content too short.")

if __name__ == "__main__":
    main()
