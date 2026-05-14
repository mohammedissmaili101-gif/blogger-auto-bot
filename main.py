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
# تم تحسين الزوايا لتكون أكثر انفتاحاً على خيال الذكاء الاصطناعي
TOPIC_ANGLES = [
    "a disruptive NEW AI model benchmark leak that is crushing OpenAI and Google",
    "a BREAKTHROUGH neuro-tech study from a top-tier lab that links AI to human cognition",
    "a revolutionary AI student tool that is making traditional exams obsolete",
    "a massive Silicon Valley boardroom coup or acquisition involving a major AI player",
    "a landmark AI achievement in curing a specific disease or solving a climate crisis",
    "the brutal 'LLM Cold War' between two specific tech giants with exclusive leak details",
    "how a new AI-automated coding platform is making human junior developers redundant",
    "a viral AI consumer trend that is reshaping social interaction or digital identity",
]

# إضافة "نكهة" عشوائية لضمان عدم تكرار العناوين نهائياً
RANDOM_FLAVORS = ["Investigative Report", "Special Leak", "Industry Analysis", "Exclusive Deep-Dive", "Inside Story"]
chosen_topic = random.choice(TOPIC_ANGLES)
chosen_flavor = random.choice(RANDOM_FLAVORS)

# ── Prompt ───────────────────────────────────────────────
# تم تعديل الـ Prompt ليجبر الذكاء الاصطناعي على ابتكار عناوين فريدة ومحددة
prompt = f"""
Current Date: {today_date}
Story Focus Style: {chosen_flavor}

You are a Pulitzer Prize-winning investigative tech journalist. 
YOUR ASSIGNED STORY: Write an EXCLUSIVE story about: {chosen_topic} in {current_year}.

ABSOLUTE TITLE RULES:
- The title must be unique, punchy, and highly specific.
- ALWAYS include a fictional or real company name, person, or specific tech-model name in the title.
- NEVER use generic titles like "The Future of AI" or "AI in 2026".
- Use 'action' verbs and high-stakes language (e.g., 'Shatters', 'Betrayal', 'Coup', 'Unveiled', 'Crisis').
- The title must feel like it belongs on the front page of The New York Times or Wired.
- Under 65 characters, no symbols.

ABSOLUTE CONTENT RULES:
1. NO generic advice or how-to lists.
2. Invent realistic, specific details: quotes, study figures, and recent (fictional) events.
3. Vary sentence length. Hook the reader in the first paragraph.
4. Minimum 900 words. Maximum 1200 words.

STRUCTURE REQUIRED (use these exact HTML tags):
- One powerful <p> opening hook
- Then alternate: <h2> section heading → 2-3 <p> paragraphs
- Use <blockquote> for expert quotes, <strong> for terms, <em> for emphasis.
- End with a forward-looking <h2> conclusion.

CRITICAL FORMATTING:
[TITLE] your unique headline
[KEYWORDS] your keywords here
[META] your meta description here
[CONTENT]
your full HTML article here
"""

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    normalized = re.sub(r'\[\s*(TITLE|KEYWORDS|META|CONTENT)\s*\]', lambda m: f'[{m.group(1).upper()}]', raw, flags=re.IGNORECASE)
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

    # تحسين العنوان في حالة الفشل في الاستخراج (Fallback) ليكون عشوائياً أيضاً
    fallback_titles = [
        f"The {current_year} {chosen_flavor}: A Tech Revolution Unveiled",
        f"Exclusive: Inside the {chosen_topic[:20]} Shaking the Industry",
        f"Smart Flow Lab Special Report: The {current_year} Pivot"
    ]
    title = title_match.group(1).strip() if title_match else random.choice(fallback_titles)
    
    keywords = kw_match.group(1).strip() if kw_match else "technology innovation bright"
    meta_raw = meta_match.group(1).strip() if meta_match else f"Exclusive analysis on {chosen_topic}."

    title = re.sub(r'[#*`]', '', title).strip()
    title = re.sub(r'^[\s\-:]+|[\s\-:]+$', '', title).strip()
    meta_desc = meta_raw[:160].strip()

    content = content_raw.strip()
    content = re.sub(r'```[\w]*|
```', '', content)
    content = re.sub(r'##\s+(.*?)(\n|$)', r'<h2>\1</h2>', content)
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

    return title, keywords, meta_desc, content

# ── Content Generation (with retry) ──────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"🤖 AI attempt {attempt}/{max_retries}...")
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.85, # زيادة طفيفة في الـ temperature للإبداع
                max_tokens=4096,
            )
            raw = completion.choices[0].message.content
            result = parse_response(raw)
            if result[0] is not None and len(result[3]) > 500:
                return result
            print(f"⚠️ Attempt {attempt} failed or content too short. Retrying...")
        except Exception as e:
            print(f"❌ API error: {e}")
    return None, None, None, None

# ── Pexels Image ─────────────────────────────────────────
def get_best_pexels_image(keywords):
    fallback_keywords = [keywords, "technology innovation bright", "digital future"]
    if not PEXELS_KEY:
        return f"https://picsum.photos/seed/{random.randint(1,9999)}/1200/628"
    headers = {"Authorization": PEXELS_KEY}
    for kw in fallback_keywords:
        try:
            url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(kw)}&per_page=10&orientation=landscape"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            photos = data.get("photos", [])
            if photos: return random.choice(photos)["src"]["large2x"]
        except: continue
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
<style>
  body {{ font-family: 'Source Serif 4', Georgia, serif; background: #fafaf8; color: #0d0d0d; font-size: 19px; line-height: 1.75; margin:0; }}
  .top-bar {{ background: #0d0d0d; color: #fff; text-align: center; padding: 10px; font-family: sans-serif; font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; }}
  .article-wrap {{ max-width: 740px; margin: 0 auto; padding: 40px 24px; }}
  h1 {{ font-family: 'Playfair Display', serif; font-size: 48px; line-height: 1.1; margin-bottom: 20px; }}
  .featured-image {{ width: 100%; max-height: 480px; object-fit: cover; margin-bottom: 30px; }}
  .content p:first-of-type::first-letter {{ font-size: 72px; float: left; line-height: 0.8; margin-right: 8px; color: #c0392b; }}
  h2 {{ border-bottom: 2px solid #0d0d0d; padding-bottom: 10px; margin-top: 40px; }}
  blockquote {{ border-left: 4px solid #c0392b; background: #fff8f7; padding: 20px; font-style: italic; font-size: 20px; }}
</style>
</head>
<body>
<div class="top-bar">Smart Flow Lab | {today_date}</div>
<article class="article-wrap">
  <h1>{title}</h1>
  <img src="{image_url}" class="featured-image">
  <div class="content">{article_body}</div>
</article>
</body>
</html>"""

# ── Send Email ────────────────────────────────────────────
def send_email(title, html_body):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published: {title}")
    except Exception as e: print(f"❌ Error: {e}")

# ── Main ──────────────────────────────────────────────────
def main():
    print(f"📌 Today's Angle: {chosen_topic}")
    title, keywords, meta_desc, article_body = generate_content()
    if title and article_body:
        image_url = get_best_pexels_image(keywords)
        full_html = build_html(title, meta_desc, image_url, article_body)
        send_email(title, full_html)

if __name__ == "__main__":
    main()
