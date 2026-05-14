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

# ── Groq Call Helper ──────────────────────────────────────
def groq_call(prompt, max_tokens=1500):
    for attempt in range(1, 4):
        try:
            print(f"🤖 Attempt {attempt}/3...")
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",  # موديل سريع وعنده limit كبير
                temperature=0.8,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Groq Error attempt {attempt}: {e}")
            time.sleep(15)
    return None

# ── Call 1: توليد العنوان والـ meta فقط (tokens قليلة) ────
def generate_meta():
    prompt = f"""Current Date: {today_date}
Story: {chosen_topic}
Angle: {random_modifier}

Generate ONLY these 3 lines, nothing else:
[TITLE] a punchy unique headline under 65 chars specific to this story
[KEYWORDS] keyword1, keyword2, keyword3, keyword4
[META] meta description under 160 chars"""

    raw = groq_call(prompt, max_tokens=200)
    if not raw:
        return None, None, None

    title_match = re.search(r"\[TITLE\]\s*(.*)", raw, re.IGNORECASE)
    kw_match    = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.IGNORECASE)
    meta_match  = re.search(r"\[META\]\s*(.*)", raw, re.IGNORECASE)

    title     = re.sub(r'[#*`]', '', title_match.group(1).split('[')[0].strip())[:65] if title_match else f"AI Exclusive {today_date}"
    keywords  = kw_match.group(1).split('[')[0].strip() if kw_match else "tech, ai, innovation"
    meta_desc = meta_match.group(1).split('[')[0].strip()[:160] if meta_match else "Deep dive analysis."

    return title, keywords, meta_desc

# ── Call 2: توليد المقال فقط (منفصل) ────────────────────
def generate_article(title):
    prompt = f"""Current Date: {today_date}
Article Title: {title}
Story: {chosen_topic}
Angle: {random_modifier}

You are an investigative tech journalist. Write the article body ONLY (700-900 words).
Use ONLY these HTML tags: <p>, <h2>, <h3>, <strong>, <em>, <blockquote>
- No markdown, no asterisks, no hashtags
- Start directly with a <p> hook paragraph
- Include at least one <blockquote> with an expert quote
- No title in the content, just the article body"""

    return groq_call(prompt, max_tokens=1500)

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
    print("🚀 Starting Groq-Powered Bot...")
    print(f"📌 Topic: {chosen_topic[:80]}")
    print(f"🎯 Angle: {random_modifier}")

    # Call 1: meta
    print("📝 Generating meta...")
    title, keywords, meta_desc = generate_meta()
    if not title:
        print("❌ Meta generation failed.")
        return
    print(f"📰 Title: {title}")

    # انتظر قليلاً بين الـ calls باش ما تتجاوزش الـ rate limit
    time.sleep(5)

    # Call 2: article
    print("✍️  Generating article...")
    content = generate_article(title)
    if not content or len(content) < 400:
        print("❌ Article generation failed or too short.")
        return

    print("🖼️  Fetching image...")
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

if __name__ == "__main__":
    main()
