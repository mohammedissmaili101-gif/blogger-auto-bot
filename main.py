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

# ── Topic Rotation System (أكثر حيوية وتنوعاً) ────────────────
TOPIC_ANGLES = [
    "a shocking NEW AI model leak that outperforms GPT-4o in logical reasoning — focus on the mystery lab behind it",
    "the secret race for Quantum-AI supremacy between a stealth startup and a Silicon Valley giant in 2026",
    "a revolutionary AI tool that allows students to 'simulate' expert mentors, and why universities are terrified",
    "a massive failed acquisition in the tech world that reveals a hidden crisis in AI hardware supply",
    "the rise of 'Small Language Models' (SLMs) that run offline and why they are the death of Big Tech's cloud monopoly",
    "how a new AI-driven 'neural' coding assistant is making junior developers obsolete while creating a new elite class of engineers",
    "a viral AI use case in 2026 where regular people are using 'Personal AI Agents' to negotiate salaries and legal contracts",
    "the battle over 'Synthetic Data' — why the internet is running out of human words to train AI and the bizarre solution found",
]

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt (تم تطويره لجلب عناوين جذابة وترافيك عالي) ───────────
prompt = f"""
Current Date: {today_date}

You are an elite, Pulitzer-winning investigative tech journalist for Wired or The Verge. 

YOUR TASK: 
Write an EXCLUSIVE deep-dive analysis on: {chosen_topic}

CRITICAL RULES FOR THE TITLE (TRAFFIC & SEO):
1. The [TITLE] MUST be a "Viral Headline" that uses a Curiosity Gap or a shocking revelation.
2. It MUST be unique to this specific story. Include specific names (e.g., the name of the model, company, or person you invent for this story).
3. NO generic titles like "The Future of AI" or "New Technology Trends". 
4. Example of a HIGH-TRAFFIC title: "The 'Zynith' Leak: Why Google Engineers are Panic-Testing a Rival's Code"
5. Title must be under 60 characters. No quotes, no hashtags, no asterisks.

ARTICLE RULES:
- Minimum 1000 words of high-quality, investigative prose.
- Invent realistic details: quotes from plausible experts, citing specific (invented) percentages and dates.
- Use a powerful "Hook" in the first paragraph.
- Format strictly with <h2>, <p>, <blockquote>, <strong>. No Markdown fences.

STRUCTURE:
[TITLE] (write your unique, viral, specific headline here)
[KEYWORDS] (3-4 visual keywords for image search)
[META] (150-char SEO description)
[CONTENT]
(Full HTML article starting with a <p> hook)
"""

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    # Normalize tags
    normalized = re.sub(r'\[\s*(TITLE|KEYWORDS|META|CONTENT)\s*\]', lambda m: f'[{m.group(1).upper()}]', raw, flags=re.IGNORECASE)
    normalized = re.sub(r'\[CONTENT[:\s]*\]', '[CONTENT]', normalized, flags=re.IGNORECASE)

    title_match   = re.search(r"\[TITLE\](.*?)(?=\[KEYWORDS\]|\[META\]|\[CONTENT\]|$)", normalized, re.DOTALL)
    kw_match      = re.search(r"\[KEYWORDS\](.*?)(?=\[META\]|\[CONTENT\]|\[TITLE\]|$)", normalized, re.DOTALL)
    meta_match    = re.search(r"\[META\](.*?)(?=\[CONTENT\]|\[TITLE\]|\[KEYWORDS\]|$)", normalized, re.DOTALL)
    content_match = re.search(r"\[CONTENT\](.*)", normalized, re.DOTALL)

    # Cleanup title (very important to remove AI quotes)
    title = title_match.group(1).strip() if title_match else "Exclusive Tech Breakthrough 2026"
    title = re.sub(r'[#*`"]', '', title).strip() # حذف الاقتباسات والرموز

    keywords = kw_match.group(1).strip() if kw_match else "innovation technology AI"
    meta_desc = meta_match.group(1).strip()[:160] if meta_match else "Exclusive tech reporting."
    
    # Handle content
    if content_match:
        content = content_match.group(1).strip()
        content = re.sub(r'```[\w]*|```', '', content)
        # Convert any remaining markdown headers to HTML just in case
        content = re.sub(r'##\s+(.*?)(\n|$)', r'<h2>\1</h2>', content)
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    else:
        return None, None, None, None

    return title, keywords, meta_desc, content

# ── Content Generation (with retry) ──────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.85, # زيادة الحرارة قليلاً لرفع الإبداع في العناوين
                max_tokens=4000,
            )
            raw = completion.choices[0].message.content
            t, k, m, c = parse_response(raw)
            if t and c: return t, k, m, c
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
    return None, None, None, None

# ── Pexels Image ─────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return f"https://picsum.photos/seed/{random.randint(1,999)}/1200/628"
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=5"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10)
        photos = res.json().get("photos", [])
        return photos[0]["src"]["large2x"] if photos else "https://picsum.photos/1200/628"
    except:
        return "https://picsum.photos/1200/628"

# ── Build Magazine Style HTML ────────────────────────────
def build_html(title, meta_desc, image_url, article_body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="description" content="{meta_desc}">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Serif+4&family=DM+Sans:wght@500&display=swap" rel="stylesheet">
<style>
  body {{ font-family: 'Source Serif 4', serif; background: #fafaf8; color: #1a1a1a; line-height: 1.8; margin: 0; padding: 0; }}
  .top-bar {{ background: #000; color: #fff; text-align: center; padding: 8px; font-family: 'DM Sans', sans-serif; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }}
  .container {{ max-width: 750px; margin: 40px auto; padding: 20px; background: #fff; box-shadow: 0 0 40px rgba(0,0,0,0.05); }}
  .category {{ color: #c0392b; font-weight: bold; text-transform: uppercase; font-size: 12px; font-family: 'DM Sans'; }}
  h1 {{ font-family: 'Playfair Display', serif; font-size: 45px; line-height: 1.1; margin: 15px 0; color: #000; }}
  .byline {{ font-family: 'DM Sans'; font-size: 13px; color: #777; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 25px; }}
  img {{ width: 100%; border-radius: 4px; margin-bottom: 30px; }}
  .content p:first-child::first-letter {{ font-size: 60px; float: left; line-height: 1; padding-right: 10px; color: #c0392b; font-family: 'Playfair Display'; }}
  h2 {{ font-family: 'Playfair Display'; font-size: 28px; margin-top: 40px; border-left: 4px solid #c0392b; padding-left: 15px; }}
  blockquote {{ font-style: italic; background: #f9f9f9; border-left: 5px solid #ccc; margin: 30px 0; padding: 20px; font-size: 20px; }}
  footer {{ text-align: center; font-size: 12px; color: #aaa; margin-top: 50px; padding: 20px; border-top: 1px solid #eee; }}
</style>
</head>
<body>
<div class="top-bar">Smart Flow Lab | Exclusive Intelligence | {today_date}</div>
<div class="container">
  <span class="category">Breaking Tech Report</span>
  <h1>{title}</h1>
  <div class="byline">By Smart Flow Lab Editorial Team &bull; {today_date} &bull; 7 min read</div>
  <img src="{image_url}" alt="Article Image">
  <div class="content">{article_body}</div>
  <footer>&copy; {current_year} Smart Flow Lab. All rights reserved.</footer>
</div>
</body>
</html>"""

# ── Send Email ────────────────────────────────────────────
def send_email(title, html_body):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(MY_GMAIL, GMAIL_PASS)
        server.send_message(msg)

# ── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    t, k, m, body = generate_content()
    if t and body:
        img = get_best_pexels_image(k)
        html = build_html(t, m, img, body)
        send_email(t, html)
        print(f"✅ Success: {t}")
    else:
        print("❌ Failed to generate content.")
