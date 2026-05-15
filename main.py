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

# ── Secrets ───────────────────────────────────────────────
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
    f"a BREAKTHROUGH scientific study about productivity using technology in {current_year}",
    f"a revolutionary AI-powered tool for students in {current_year}",
    f"a major Silicon Valley corporate shakeup happening RIGHT NOW in {current_year}",
    f"the fierce battle between OpenAI vs Google vs Meta in {current_year}",
    f"a cutting-edge AI application in healthcare that just got massive funding in {current_year}",
    f"how a newly released AI coding tool in {current_year} is transforming software engineering",
    f"a viral AI use case that regular people are adopting RIGHT NOW in {current_year}",
]

random_modifier = random.choice([
    "Focus on a hidden scandal or controversy.",
    "Highlight the extreme financial implications.",
    "Make the title sound like a high-stakes thriller headline.",
    "Focus on the human impact and societal consequences.",
])

chosen_topic = random.choice(TOPIC_ANGLES)

def groq_call(prompt, max_tokens=1500):
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.8,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(10)
    return None

def generate_meta():
    prompt = f"Topic: {chosen_topic}\nModifier: {random_modifier}\nGenerate ONLY: [TITLE] (max 65 chars), [KEYWORDS], [META] (max 160 chars)"
    raw = groq_call(prompt, max_tokens=200)
    if not raw: return None, None, None
    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)", raw, re.I)
    return (t.group(1).strip() if t else "AI Tech Update"), (k.group(1).strip() if k else "AI"), (m.group(1).strip() if m else "")

def generate_article(title):
    prompt = f"Title: {title}\nTopic: {chosen_topic}\nWrite a long investigative article (800 words). Use ONLY <p>, <h2>, <blockquote>, <strong>. No markdown."
    return groq_call(prompt, max_tokens=1800)

def get_best_pexels_image(keywords):
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        return res["photos"][0]["src"]["large2x"]
    except: return "https://picsum.photos/1200/630"

# ── Magazine HTML Builder (من الكود القديم لضمان النشر) ──
def build_full_html(title, content, img, meta):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Georgia', serif; line-height: 1.8; color: #1a1a1a; max-width: 800px; margin: auto;">
        <div style="text-align: center; border-bottom: 2px solid #333; padding: 20px;">
            <h1 style="font-size: 36px; margin-bottom: 10px;">{title}</h1>
            <p style="color: #666;">Smart Flow Lab Exclusive • {today_date}</p>
        </div>
        <img src="{img}" style="width: 100%; border-radius: 8px; margin: 30px 0;">
        <div style="font-size: 19px;">{content}</div>
        <hr style="margin: 50px 0; border: 0; border-top: 1px solid #eee;">
        <footer style="text-align: center; color: #999; font-size: 12px;">
            © {current_year} Smart Flow Lab. Meta: {meta}
        </footer>
    </body>
    </html>
    """

def main():
    print("🚀 Starting Engine...")
    title, keywords, meta = generate_meta()
    if not title: return
    
    print(f"📰 Generating Content for: {title}")
    content = generate_article(title)
    if not content: return
    
    img = get_best_pexels_image(keywords)
    full_html = build_full_html(title, content, img, meta)

    msg = MIMEText(full_html, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Article Sent and Published: {title}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
