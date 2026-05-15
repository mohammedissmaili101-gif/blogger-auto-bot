import os
import re
import datetime
import urllib.parse
import requests
import random
import time
import json
from groq import Groq
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# ── Secrets ───────────────────────────────────────────────
GROQ_KEY      = os.environ.get("GROQ_API_KEY")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY")
CLIENT_ID     = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

client       = Groq(api_key=GROQ_KEY)
today_iso    = datetime.datetime.now().isoformat()
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = datetime.date.today().year

# ── Blogger API Setup ─────────────────────────────────────
def post_to_blogger_api(title, html_content):
    try:
        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        if not creds.valid:
            creds.refresh(Request())

        service = build('blogger', 'v3', credentials=creds)
        blogs = service.blogs().listByUser(userId='self').execute()
        blog_id = blogs['items'][0]['id']

        body = {
            "kind": "blogger#post",
            "title": title,
            "content": html_content,
            "labels": ["News"]
        }

        service.posts().insert(blogId=blog_id, body=body).execute()
        print(f"✅ Article Published: {title}")
    except Exception as e:
        print(f"❌ Blogger API Error: {e}")

# ── Smart Topics Rotation ────────────────────────
TOPIC_ANGLES = [
    {
        "topic": "Latest developments in Generative AI architectures and LLM training costs",
        "image_queries": ["artificial intelligence server room", "neural network computing", "data center GPU cluster"]
    },
    {
        "topic": "Global semiconductor supply chain shifts and geopolitical impact on tech",
        "image_queries": ["semiconductor chip manufacturing", "silicon wafer factory", "microchip production"]
    },
    {
        "topic": "Emerging cybersecurity protocols for protecting decentralized financial data",
        "image_queries": ["cybersecurity network protection", "blockchain technology digital", "data encryption security"]
    },
    {
        "topic": "Advancements in biotechnology and AI-driven drug discovery efficiency",
        "image_queries": ["biotechnology laboratory research", "drug discovery microscope", "pharmaceutical AI research"]
    },
    {
        "topic": "Sustainable energy tech: Next-generation battery storage and hydrogen power",
        "image_queries": ["hydrogen fuel cell technology", "battery storage renewable energy", "sustainable energy grid"]
    },
    {
        "topic": "Big Tech antitrust regulations: Europe vs. Silicon Valley's legal landscape",
        "image_queries": ["tech regulation government policy", "silicon valley headquarters", "european union technology law"]
    }
]

# ── FIX 1: Markdown → HTML converter ─────────────────────
def markdown_to_html(text):
    """Convert any leftover Markdown formatting to proper HTML."""
    # **bold** → <strong>bold</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *italic* → <em>italic</em>
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Bullet lines starting with * or - → wrap in <ul><li>
    lines = text.split('\n')
    html_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[\*\-]\s+', stripped):
            item = re.sub(r'^[\*\-]\s+', '', stripped)
            if not in_list:
                html_lines.append('<ul style="margin: 15px 0; padding-left: 25px;">')
                in_list = True
            html_lines.append(f'<li style="margin-bottom: 8px;">{item}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(line)
    if in_list:
        html_lines.append('</ul>')
    return '\n'.join(html_lines)

def post_process_html(html):
    """
    Cleans AI-generated HTML after generation:
    1. Removes duplicate consecutive <h2> with same text.
    2. Replaces named person attributions with anonymous role.
    """
    # ── 1. Remove duplicate <h2> ──────────────────────────
    seen_h2 = []
    def dedup_h2(m):
        text = m.group(1).strip().lower()
        if text in seen_h2:
            return ''
        seen_h2.append(text)
        return m.group(0)
    html = re.sub(r'<h2[^>]*>(.*?)</h2>', dedup_h2, html, flags=re.IGNORECASE | re.DOTALL)

    # ── 2. Replace "— Dr. Real Name, Title at Org" with anonymous ──
    # Catches:  — Dr. Maria Zuber, Director of MIT ...
    #           — John Smith, Head of Research at ...
    html = re.sub(
        r'—\s*(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+[^<\n]{0,150}',
        '— <em>Senior industry analyst</em>',
        html
    )

    return html

def groq_call(system_msg, user_msg, max_tokens=2000):
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.5,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(10)
    return None

def generate_meta(topic):
    system_msg = "You are a professional News SEO strategist. Generate metadata without fluff."
    user_msg = (
        f"Generate metadata for: {topic}. "
        "Output ONLY in this format:\n"
        "[TITLE] (max 65 chars)\n"
        "[KEYWORDS] (3 comma-separated terms)\n"
        "[META] (one compelling sentence)"
    )

    raw = groq_call(system_msg, user_msg, max_tokens=300)
    if not raw:
        return None, None, None

    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)", raw, re.I)

    title    = t.group(1).strip() if t else f"Update: {topic}"
    keywords = k.group(1).strip() if k else "Tech, News, Innovation"
    meta     = m.group(1).strip() if m else f"Latest analysis on {topic}."

    return title, keywords, meta

# ── FIX 2: Anti-hallucination article generator ───────────
def generate_article(title, topic):
    system_msg = """You are a Senior Tech Analyst writing an industry analysis report. 

ABSOLUTE RULES — violation = unusable article:
1. HTML ONLY: use <h2>, <p>, <blockquote>, <ul>, <li>, <strong>. Zero Markdown.
2. NO INVENTED PEOPLE: Never write "Jane Smith, Director at X said...". 
   Instead use ONLY: "Industry analysts suggest...", "Observers note...", 
   "According to market research...", "Sector reports indicate..."
3. NO INVENTED PRODUCTS: Do NOT name fake models, papers, or projects 
   (e.g., "EffTrans", "LinguaCore"). Discuss real, confirmed trends only.
4. NO FAKE STATISTICS: Do NOT write "reduces costs by 90%" unless it is 
   publicly confirmed. Use ranges: "estimates vary between X and Y".
5. BLOCKQUOTE = anonymous industry voice only: 
   <blockquote>"..." — <em>Senior analyst, AI infrastructure sector</em></blockquote>
6. TONE: Analytical, cautious, objective. No hype."""

    user_msg = (
        f"Write a 700-word industry analysis in HTML.\n"
        f"Title: {title}\n"
        f"Topic: {topic}\n"
        f"Date: {today_date}\n\n"
        "Structure: intro <p> → 2 sections <h2>+<p> → insight <blockquote> → conclusion <p>.\n"
        "Pure HTML only. No invented names, no invented products, no fake numbers."
    )

    raw = groq_call(system_msg, user_msg)
    if not raw:
        return None

    # Step 1: Convert any leftover Markdown → HTML
    cleaned = markdown_to_html(raw)
    # Step 2: Remove duplicate headings + named attributions
    cleaned = post_process_html(cleaned)
    return cleaned

# ── FIX 3: Topic-aware image search ──────────────────────
def get_best_pexels_image(image_queries):
    """
    Uses curated per-topic queries instead of random keywords
    to ensure the image is contextually relevant.
    """
    try:
        query = random.choice(image_queries)
        url = (
            f"https://api.pexels.com/v1/search"
            f"?query={urllib.parse.quote(query)}&per_page=15&orientation=landscape"
        )
        res = requests.get(
            url,
            headers={"Authorization": PEXELS_KEY},
            timeout=10
        ).json()

        if res.get("photos"):
            # Pick from top 5 for some variety while keeping relevance
            top_photos = res["photos"][:5]
            return random.choice(top_photos)["src"]["large2x"]

        raise Exception("No photos found")
    except Exception as e:
        print(f"⚠️ Pexels error: {e} — using fallback image")
        hash_seed = abs(hash(query)) % 1000
        return f"https://picsum.photos/seed/{hash_seed}/1200/630"

def build_full_html(title, content, img, meta):
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "image": [img],
        "datePublished": today_iso,
        "author": {
            "@type": "Person",
            # FIX 4: Unified author name + bio everywhere
            "name": "Mohamed Ismaili",
            "jobTitle": "Senior Technology Analyst"
        }
    }

    return f"""
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<div style="font-family: 'Georgia', serif; line-height: 1.8; color: #1a1a1a; max-width: 800px; margin: auto; padding: 20px;">

    <header style="border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 30px;">
        <h1 style="font-size: 36px; line-height: 1.2; font-weight: bold; margin-bottom: 10px;">{title}</h1>
        <p style="color: #555; font-size: 14px; font-weight: bold;">
            SMART FLOW LAB &bull; {today_date} &bull; BY MOHAMED ISMAILI
        </p>
    </header>

    <figure style="margin: 0 0 30px 0;">
        <img src="{img}" alt="{title}" style="width: 100%; height: auto; border-radius: 4px;">
        <figcaption style="font-size: 12px; color: #888; margin-top: 6px; text-align: center;">
            Image related to: {title}
        </figcaption>
    </figure>

    <div style="font-size: 18px;">
        {content}
    </div>

    <div style="margin-top: 50px; padding: 25px; background: #f9f9f9; border-left: 4px solid #cc0000;">
        <strong style="font-size: 20px;">Mohamed Ismaili</strong><br>
        <span style="color: #666;">
            Senior Technology Analyst at Smart Flow Lab — covering AI systems,
            semiconductor markets, and digital infrastructure policy.
        </span>
    </div>

    <footer style="margin-top: 40px; text-align: center; font-size: 11px; color: #999;
                   border-top: 1px solid #eee; padding-top: 20px;">
        &copy; {current_year} Smart Flow Lab. All rights reserved.
    </footer>
</div>
"""

def main():
    print("🚀 Running Smart Flow Lab Publisher...")

    # Pick a full topic object (topic + image queries together)
    chosen = random.choice(TOPIC_ANGLES)
    topic         = chosen["topic"]
    image_queries = chosen["image_queries"]

    title, keywords, meta = generate_meta(topic)
    if not title:
        print("❌ Could not generate metadata. Stopping.")
        return

    print(f"📰 Drafting: {title}")

    content = generate_article(title, topic)
    if not content:
        print("❌ Could not generate article. Stopping.")
        return

    img      = get_best_pexels_image(image_queries)
    full_html = build_full_html(title, content, img, meta)

    post_to_blogger_api(title, full_html)

if __name__ == "__main__":
    main()
