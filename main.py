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

# ── Topic Rotation System (تم توسيعها لضمان التنوع اللانهائي) ─────────────────
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

# إضافة لمسة عشوائية لضمان عنوان مختلف كل مرة
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
    # Normalize tag casing and spacing
    normalized = re.sub(
        r'\[\s*(TITLE|KEYWORDS|META|CONTENT)\s*\]',
        lambda m: f'[{m.group(1).upper()}]',
        raw, flags=re.IGNORECASE
    )

    normalized = re.sub(r'\[CONTENT[:\s]*\]', '[CONTENT]', normalized, flags=re.IGNORECASE)

    title_match   = re.search(r"\[TITLE\](.*?)(?=\[KEYWORDS\]|\[META\]|\[CONTENT\]|$)", normalized, re.DOTALL)
    kw_match      = re.search(r"\[KEYWORDS\](.*?)(?=\[META\]|\[CONTENT\]|\[TITLE\]|$)", normalized, re.DOTALL)
    meta_match    = re.search(r"\[META\](.*?)(?=\[CONTENT\]|\[TITLE\]|\[KEYWORDS\]|$)", normalized, re.DOTALL)
    content_match = re.search(r"\[CONTENT\](.*)", normalized, re.DOTALL)

    if not content_match:
        html_match = re.search(r'(<(?:p|h2|h3|blockquote)[^>]*>.*)', normalized, re.DOTALL | re.IGNORECASE)
        content_raw = html_match.group(1) if html_match else ""
    else:
        content_raw = content_match.group(1)

    title    = title_match.group(1).strip()  if title_match else "Exclusive Report: The Future of Innovation"
    keywords = kw_match.group(1).strip()     if kw_match   else "tech, innovation, ai"
    meta_raw = meta_match.group(1).strip()   if meta_match else f"Exclusive analysis for {current_year}."

    # التنظيف وتصحيح Regex (حل مشكلة Syntax Error)
    title = re.sub(r'[#*`]', '', title).strip()
    title = re.sub(r'^[\s\-:]+|[\s\-:]+$', '', title).strip()

    meta_desc = meta_raw[:160].strip()

    content = content_raw.strip()
    content = re.sub(r'```[\w]*|```', '', content)
    content = re.sub(r'##\s+(.*?)(\n|$)', r'<h2>\1</h2>', content)
    
    # تصحيح علامات النجمة لعدم الوقوع في خطأ الـ Literal String
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = content.strip()

    return title, keywords, meta_desc, content


# ── Content Generation (with retry) ──────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"🤖 AI attempt {attempt}/{max_retries}...")
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.90, # رفع الحرارة قليلاً لزيادة الإبداع في العناوين
                max_tokens=4096,
            )
            raw = completion.choices[0].message.content

            result = parse_response(raw)
            if result[0] and len(result[3]) > 100:
                return result

        except Exception as e:
            print(f"❌ API error on attempt {attempt}: {e}")

    return None, None, None, None


# ── Pexels Image (bright, relevant) ──────────────────────
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

# ── Send Email ────────────────────────────────────────────
def send_email(title, html_body):
    msg            = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published: {title}")
    except Exception as e:
        print(f"❌ Error: {e}")

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
