import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
# FIX: استبدلنا MIMEText بـ MIMEMultipart + MIMEText باش نتحكم في headers بشكل كامل
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
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
    f"the most disruptive NEW AI model released this week in {current_year} — cover its benchmarks, real-world impact, and what it means for the industry",
    f"a BREAKTHROUGH scientific study published in {current_year} that is reshaping how we understand human cognition, learning, or productivity using technology",
    f"a revolutionary AI-powered tool JUST LAUNCHED for students or researchers in {current_year} that is changing how people study, write, or learn",
    f"a major SILICON VALLEY corporate shakeup, acquisition, or product pivot happening RIGHT NOW in {current_year} that is sending shockwaves through the tech world",
    f"a cutting-edge AI application in healthcare, climate tech, or education that just received massive funding or produced landmark results in {current_year}",
    f"the fierce battle between two or more AI giants (e.g., OpenAI vs Google vs Meta vs Anthropic) over a specific capability or market in {current_year} — with exclusive analysis",
    f"how a newly released AI coding or developer tool in {current_year} is transforming software engineering and what it means for the future of work",
    f"a viral, trend-setting AI use case that regular people are adopting RIGHT NOW in {current_year} — explain the why, the how, and the societal impact",
]

random_modifier = random.choice([
    "Focus on a hidden scandal or controversy.",
    "Write it from the perspective of an insider leak.",
    "Highlight the extreme financial implications.",
    "Focus on a specific, newly-invented technical term.",
    "Make the title sound like a high-stakes thriller headline."
])

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}
Specific Angle Focus: {random_modifier}

You are a Pulitzer Prize-winning investigative tech journalist for a world-class publication like The Atlantic or MIT Technology Review.

YOUR ASSIGNED STORY TODAY:
Write an EXCLUSIVE, deeply reported, analytical article about: {chosen_topic}

ABSOLUTE RULES — VIOLATIONS WILL RESULT IN REJECTION:
1. NO generic advice, no how-to lists, no "Top 10" formats.
2. The article must read like BREAKING NEWS or an EXCLUSIVE DEEP-DIVE ANALYSIS.
3. You MUST invent realistic, specific details: quote real or plausible expert names with titles, cite plausible study figures, mention real company names, real model names, and real recent events. 
4. **CRITICAL FOR UNIQUE TITLES**: Your title MUST include a specific (invented if needed) name of a person, project, or company to ensure it is 100% unique and never repeated.
5. The opening paragraph must be a powerful HOOK that grabs the reader immediately.
6. Minimum 900 words. Maximum 1200 words.
7. The title must be UNDER 65 characters — no hashtags (#), no asterisks (*), no special symbols.

STRUCTURE REQUIRED (use these exact HTML tags):
- One powerful <p> opening hook (no heading before it)
- Then alternate: <h2> section heading → 2-3 <p> paragraphs → repeat
- Use <blockquote> for at least ONE expert quote
- Use <strong> for key terms, company names, model names
- Use <em> for emphasis on critical insights
- End with a forward-looking <h2> conclusion section

CRITICAL FORMATTING RULE — MANDATORY:
[TITLE] your unique catchy title here
[KEYWORDS] your keywords here
[META] your meta description here
[CONTENT]
your full HTML article here using ONLY <p>, <h2>, <h3>, <strong>, <em>, <blockquote>.
"""

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    raw_clean = raw.replace('**', '').replace('#', '')

    title_match   = re.search(r"\[TITLE\]\s*(.*)", raw_clean, re.IGNORECASE)
    kw_match      = re.search(r"\[KEYWORDS\]\s*(.*)", raw_clean, re.IGNORECASE)
    meta_match    = re.search(r"\[META\]\s*(.*)", raw_clean, re.IGNORECASE)
    content_match = re.search(r"\[CONTENT\]\s*(.*)", raw, re.DOTALL | re.IGNORECASE)

    title = ""
    if title_match:
        title = title_match.group(1).split('[')[0].strip()

    if not title or len(title) < 5:
        lines = [l.strip() for l in raw_clean.split('\n') if len(l.strip()) > 10 and not l.startswith('[')]
        title = lines[0] if lines else f"Tech Insights {current_year}"

    title = re.sub(r'[^\w\s\-\!\?]', '', title)[:65].strip()

    keywords  = kw_match.group(1).split('[')[0].strip() if kw_match else "tech, innovation, ai"
    meta_desc = meta_match.group(1).split('[')[0].strip()[:160] if meta_match else f"Exclusive analysis for {current_year}."

    if content_match:
        content = content_match.group(1).strip()
    else:
        html_start = re.search(r"(<p>|<h2>).*", raw, re.DOTALL | re.IGNORECASE)
        content = html_start.group(0) if html_start else raw

    content = re.sub(r'```[\w]*|```', '', content)
    content = re.sub(r'##\s+(.*?)(\n|$)', r'<h2>\1</h2>', content)
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = content.strip()

    return title, keywords, meta_desc, content


# ── Content Generation ────────────────────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"🤖 AI attempt {attempt}/{max_retries}...")
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.90,
                max_tokens=4096,
            )
            raw = completion.choices[0].message.content
            result = parse_response(raw)
            if result[0] and len(result[3]) > 100:
                return result
        except Exception as e:
            print(f"❌ API error on attempt {attempt}: {e}")
    return None, None, None, None


# ── Pexels Image ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    fallback_keywords = [keywords, "modern technology", "future intelligence"]
    if not PEXELS_KEY:
        return f"https://picsum.photos/seed/{random.randint(1,9999)}/1200/628"

    headers = {"Authorization": PEXELS_KEY}
    for kw in fallback_keywords:
        try:
            url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(kw)}&per_page=5&orientation=landscape"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            photos = data.get("photos", [])
            if photos:
                return random.choice(photos)["src"]["large2x"]
        except:
            continue
    return f"https://picsum.photos/seed/{random.randint(1,9999)}/1200/628"


# ── Magazine-Quality HTML Builder ────────────────────────
def build_html(title, meta_desc, image_url, article_body):
    title_safe = title.replace('"', '&quot;')
    meta_safe  = meta_desc.replace('"', '&quot;')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{meta_safe}">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{ --ink: #0d0d0d; --accent: #c0392b; --bg: #fafaf8; }}
  body {{ font-family: 'Source Serif 4', Georgia, serif; background: var(--bg); color: var(--ink); font-size: 19px; line-height: 1.75; }}
  .top-bar {{ background: var(--ink); color: #fff; text-align: center; padding: 10px; font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; }}
  .article-wrap {{ max-width: 740px; margin: 0 auto; padding: 40px 24px 80px; }}
  h1.headline {{ font-family: 'Playfair Display', serif; font-size: 42px; font-weight: 800; line-height: 1.15; margin-bottom: 20px; }}
  .featured-image-wrap img {{ width: 100%; border-radius: 4px; margin-bottom: 20px; }}
  .content p {{ margin-bottom: 26px; }}
  .content h2 {{ font-family: 'Playfair Display', serif; font-size: 28px; margin: 40px 0 20px; border-bottom: 1px solid #ddd; }}
  blockquote {{ border-left: 4px solid var(--accent); background: #fff8f7; margin: 30px 0; padding: 20px; font-style: italic; }}
</style>
</head>
<body>
<div class="top-bar">Smart Flow Lab | {today_date}</div>
<article class="article-wrap">
  <h1 class="headline">{title}</h1>
  <div class="featured-image-wrap"><img src="{image_url}"></div>
  <div class="content">{article_body}</div>
</article>
</body>
</html>
"""


# ── Send to Blogger via Email ─────────────────────────────
def send_email(title, html_body):
    # FIX 1: تنظيف العنوان من أي whitespace/newlines خفية
    clean_title = title.strip().replace("\n", " ").replace("\r", " ")

    # FIX 2: استخدام MIMEMultipart بدل MIMEText مباشرة
    # Blogger يحتاج Content-Type: text/html بشكل صريح داخل multipart
    msg = MIMEMultipart("alternative")

    # FIX 3: Subject يحتاج RFC2047 encoding للتأكد من وصوله لـ Blogger صح
    msg['Subject'] = Header(clean_title, 'utf-8')

    # FIX 4: From يجب أن يكون فقط الإيميل بدون اسم — Blogger يرفض أحياناً "Name <email>"
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL

    # FIX 5: إضافة X-Blogger-Labels header (اختياري — يضيف label للمقال في Blogger)
    # msg['X-Blogger-Labels'] = "Tech, AI"  # uncomment إذا بغيتي labels

    # FIX 6: attach HTML part بـ charset صريح
    html_part = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(html_part)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published & Sent: {clean_title}")
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail Auth Failed — check GMAIL_APP_PASSWORD env var")
    except smtplib.SMTPRecipientsRefused:
        print(f"❌ Blogger rejected recipient: {BLOGGER_MAIL} — verify the Blogger email address in Settings → Email")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


# ── Main ──────────────────────────────────────────────────
def main():
    print(f"📌 Today's angle: {chosen_topic[:60]}...")
    title, keywords, meta_desc, article_body = generate_content()

    if not title or not article_body:
        print("❌ Failed to generate.")
        return

    image_url = get_best_pexels_image(keywords)
    full_html = build_html(title, meta_desc, image_url, article_body)
    send_email(title, full_html)

if __name__ == "__main__":
    main()
