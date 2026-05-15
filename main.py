import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import traceback
from email.message import EmailMessage
from groq import Groq

# ── Secrets (Updated to match your GitHub Secrets) ────────
GROQ_KEY      = os.environ.get("GROQ_API_KEY", "")
BLOGGER_MAIL  = os.environ.get("BLOGGER_EMAIL", "")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "")

# هادو هما اللي صححنا سمياتهم باش يتقرأو من الـ Secrets ديالك
SENDER_GMAIL  = os.environ.get("GMAIL_SENDER", "")
SENDER_PASS   = os.environ.get("GMAIL_SENDER_PASS", "")

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = str(datetime.date.today().year)

# ── Topic Rotation System ─────────────────────────────────
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year} — cover its benchmarks, real-world impact",
    f"a BREAKTHROUGH scientific study published in {current_year} reshaping human cognition using technology",
    f"a revolutionary AI-powered tool JUST LAUNCHED for students in {current_year} changing how people study",
    f"a major SILICON VALLEY corporate acquisition happening RIGHT NOW in {current_year}",
    f"a cutting-edge AI application in healthcare that produced landmark results in {current_year}",
    f"the fierce battle between AI giants OpenAI vs Google over a specific capability in {current_year}",
    f"how a newly released AI coding tool in {current_year} is transforming software engineering",
    f"a viral AI use case that regular people are adopting RIGHT NOW in {current_year}",
]

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt Construction ──────────────────────────────────
prompt = f"""
Current Date: {today_date}
You are a Pulitzer Prize-winning investigative tech journalist.
YOUR ASSIGNED STORY: {chosen_topic}

ABSOLUTE RULES:
1. NO generic advice, no how-to lists.
2. BREAKING NEWS style with an exclusive deep-dive feel.
3. Invent realistic details: quote plausible experts, cite figures, mention real companies.
4. Word count: 900 - 1200 words.
5. HTML tags ONLY: <p>, <h2>, <strong>, <em>, <blockquote>.

[TITLE] headline under 65 chars
[KEYWORDS] technology, AI, innovation
[META] brief SEO description
[CONTENT]
full HTML article content here
"""

# ── CSS ──────────────────────────────────────────────────
CSS = """
  body { font-family: 'Source Serif 4', Georgia, serif; background: #fafaf8; color: #0d0d0d; line-height: 1.8; padding: 10px; }
  .article-wrap { max-width: 740px; margin: 20px auto; background: #ffffff; padding: 40px; border: 1px solid #e2e2e2; border-radius: 4px; }
  .tag { display: inline-block; background: #c0392b; color: #fff; padding: 4px 10px; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 15px; }
  h1 { font-family: 'Playfair Display', serif; font-size: 38px; line-height: 1.2; margin-bottom: 20px; color: #000; }
  .byline { font-size: 14px; color: #666; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
  h2 { font-family: 'Playfair Display', serif; font-size: 26px; margin: 40px 0 15px; border-bottom: 2px solid #0d0d0d; padding-bottom: 5px; }
  p { margin-bottom: 25px; font-size: 19px; }
  blockquote { border-left: 5px solid #c0392b; background: #fff8f7; padding: 20px; font-style: italic; margin: 30px 0; font-size: 21px; }
  .featured-image { width: 100%; height: auto; border-radius: 2px; margin-bottom: 30px; }
  footer { margin-top: 50px; text-align: center; font-size: 12px; color: #999; border-top: 1px double #ddd; padding-top: 20px; }
"""

def parse_response(raw):
    raw = str(raw)
    title_match = re.search(r"\[TITLE\](.*?)(?=\[KEYWORDS\]|\[META\]|\[CONTENT\]|$)", raw, re.IGNORECASE | re.DOTALL)
    kw_match    = re.search(r"\[KEYWORDS\](.*?)(?=\[META\]|\[CONTENT\]|\[TITLE\]|$)", raw, re.IGNORECASE | re.DOTALL)
    meta_match  = re.search(r"\[META\](.*?)(?=\[CONTENT\]|\[TITLE\]|\[KEYWORDS\]|$)", raw, re.IGNORECASE | re.DOTALL)
    content_match = re.search(r"\[CONTENT\](.*)", raw, re.IGNORECASE | re.DOTALL)

    title    = title_match.group(1).strip() if title_match else f"Smart Flow Lab Exclusive: {today_date}"
    keywords = kw_match.group(1).strip() if kw_match else "AI, Technology, Future"
    meta     = meta_match.group(1).strip() if meta_match else "Exclusive AI intelligence report."
    content  = content_match.group(1).strip() if content_match else "<p>Content generation failed.</p>"
    
    return str(title), str(keywords), str(meta), str(content)

def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/628"
    try:
        query = urllib.parse.quote(str(keywords))
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        data = res.json()
        if data.get("photos"): return data["photos"][0]["src"]["large2x"]
    except: pass
    return "https://picsum.photos/1200/628"

def build_html(title, meta_desc, image_url, article_body):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>{CSS}</style>
    </head>
    <body>
        <div class="article-wrap">
            <span class="tag">Exclusive Analysis</span>
            <h1>{title}</h1>
            <div class="byline">By <strong>Smart Flow Lab Editorial</strong> | {today_date} | 5 min read</div>
            <img src="{image_url}" class="featured-image" alt="AI Coverage">
            <div class="content">
                {article_body}
            </div>
            <footer>
                &copy; {current_year} Smart Flow Lab &bull; Tech & AI Intelligence
            </footer>
        </div>
    </body>
    </html>
    """

def send_email(title, html_body):
    if not SENDER_GMAIL or not SENDER_PASS or not BLOGGER_MAIL:
        print("ERROR: Missing email configuration secrets.")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = str(title)
        msg["From"]    = str(SENDER_GMAIL)
        msg["To"]      = str(BLOGGER_MAIL)
        msg.set_content("Please use an HTML-compatible email client.")
        msg.add_alternative(str(html_body), subtype="html")

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(str(SENDER_GMAIL), str(SENDER_PASS))
            server.send_message(msg)
        print(f"✅ SUCCESS: Published '{title}' to Blogger.")
    except Exception as e:
        print(f"❌ SMTP/Email ERROR: {e}")
        traceback.print_exc()

def main():
    print(f"🚀 Starting Smart Flow Lab Engine...")
    print(f"Topic: {chosen_topic}")
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        raw_res = completion.choices[0].message.content
        title, keywords, meta, body = parse_response(raw_res)
        
        print(f"📰 Article Generated: {title}")
        
        img_url = get_best_pexels_image(keywords)
        full_html = build_html(title, meta, img_url, body)
        
        send_email(title, full_html)
    except Exception as e:
        print(f"⚠️ Critical Main Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
