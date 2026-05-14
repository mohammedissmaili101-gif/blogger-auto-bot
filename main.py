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

# ── Prompt (Enhanced for Long-Form & SEO) ────────────────
prompt = f"""
Current Date: {today_date}
Specific Angle Focus: {random_modifier}

You are a Pulitzer Prize-winning investigative tech journalist.
YOUR ASSIGNED STORY: {chosen_topic}

ABSOLUTE RULES (MANDATORY FOR GOOGLE ADS):
1. LENGTH: Minimum 1100 words. Be extremely detailed.
2. NO "Top 10" or generic advice. Write an EXCLUSIVE INVESTIGATIVE ANALYSIS.
3. VIVID DETAILS: Invent specific names, project codes, and citation figures.
4. UNIQUE TITLE: Include a specific company or person's name. (Under 65 chars, no symbols).
5. STRUCTURE: Powerful opening hook <p>, then alternate <h2> with 3-4 <p> paragraphs. Use <blockquote> and <strong>.

[TITLE] your title
[KEYWORDS] seo keywords
[META] meta description
[CONTENT]
Full HTML content using only <p>, <h2>, <h3>, <strong>, <em>, <blockquote>.
"""

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    raw_clean = raw.replace('**', '').replace('#', '')
    title_match = re.search(r"\[TITLE\]\s*(.*)", raw_clean, re.IGNORECASE)
    kw_match    = re.search(r"\[KEYWORDS\]\s*(.*)", raw_clean, re.IGNORECASE)
    meta_match  = re.search(r"\[META\]\s*(.*)", raw_clean, re.IGNORECASE)
    content_match = re.search(r"\[CONTENT\]\s*(.*)", raw, re.DOTALL | re.IGNORECASE)

    title = title_match.group(1).split('[')[0].strip() if title_match else f"Tech Insider {today_date}"
    title = re.sub(r'[^\w\s\-\!\?]', '', title)[:65].strip()
    
    keywords = kw_match.group(1).split('[')[0].strip() if kw_match else "tech news, ai"
    meta_desc = meta_match.group(1).split('[')[0].strip()[:160] if meta_match else "Exclusive tech deep-dive."

    if content_match:
        content = content_match.group(1).strip()
    else:
        html_start = re.search(r"(<p>|<h2>).*", raw, re.DOTALL | re.IGNORECASE)
        content = html_start.group(0) if html_start else raw

    # Clean Markdown artifacts
    content = re.sub(r'```[\w]*|```', '', content)
    return title, keywords, meta_desc, content

# ── Content Generation ────────────────────────────────────
def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.85,
            max_tokens=4000,
        )
        return parse_response(completion.choices[0].message.content)
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return None, None, None, None

# ── Pexels Image ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY: return f"https://picsum.photos/seed/{random.randint(1,999)}/1200/630"
    headers = {"Authorization": PEXELS_KEY}
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(keywords)}&per_page=1&orientation=landscape"
        res = requests.get(url, headers=headers, timeout=10).json()
        return res["photos"][0]["src"]["large2x"] if res.get("photos") else "https://picsum.photos/1200/630"
    except:
        return "https://picsum.photos/1200/630"

# ── Blogger-Friendly HTML Builder ────────────────────────
def build_html(title, meta_desc, image_url, article_body):
    return f"""
    <div dir="ltr" style="font-family: 'Georgia', serif; color: #1a1a1a; line-height: 1.8; font-size: 19px; max-width: 800px; margin: auto;">
        <div style="margin-bottom: 30px; text-align: center;">
            <img src="{image_url}" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);" alt="{title}">
        </div>
        <div style="text-align: justify;">
            {article_body}
        </div>
        <hr style="margin-top: 50px; border: 0; border-top: 1px solid #eee;">
        <p style="text-align: center; color: #888; font-size: 14px; font-family: sans-serif;">
            © {current_year} Smart Flow Lab Intelligence. All Rights Reserved.
        </p>
    </div>
    """

# ── Send Email (Reliable Publishing) ─────────────────────
def send_email(title, html_body):
    clean_title = title.strip().replace("\n", "").replace("\r", "")
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = clean_title
    msg['From']    = MY_GMAIL 
    msg['To']      = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=60) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ PUBLISHED: {clean_title}")
    except Exception as e:
        print(f"❌ SMTP Error: {e}")

# ── Main ──────────────────────────────────────────────────
def main():
    print(f"🚀 Generating Long-Form Article...")
    title, keywords, meta_desc, article_body = generate_content()

    if title and len(article_body) > 500:
        image_url = get_best_pexels_image(keywords)
        full_html = build_html(title, meta_desc, image_url, article_body)
        send_email(title, full_html)
    else:
        print("❌ Content too short or generation failed.")

if __name__ == "__main__":
    main()
