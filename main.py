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
    "Latest developments in Generative AI architectures and LLM training costs",
    "Global semiconductor supply chain shifts and geopolitical impact on tech",
    "Emerging cybersecurity protocols for protecting decentralized financial data",
    "Advancements in biotechnology and AI-driven drug discovery efficiency",
    "Sustainable energy tech: Next-generation battery storage and hydrogen power",
    "Big Tech antitrust regulations: Europe vs. Silicon Valley's legal landscape"
]

def groq_call(system_msg, user_msg, max_tokens=2000):
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.6, # تقليل الحرارة لضمان واقعية أكثر
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(10)
    return None

def generate_meta(topic):
    system_msg = "You are a professional News SEO strategist. Generate metadata without fluff."
    user_msg = f"Generate metadata for: {topic}. Output ONLY in this format: [TITLE] (max 65 chars), [KEYWORDS] (3 comma-separated terms), [META] (one compelling sentence)."
    
    raw = groq_call(system_msg, user_msg, max_tokens=300)
    if not raw: return None, None, None

    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)", raw, re.I)
    
    title = t.group(1).strip() if t else f"Update: {topic}"
    keywords = k.group(1).strip() if k else "Tech, News, Innovation"
    meta = m.group(1).strip() if m else f"Latest analysis on {topic}."
    
    return title, keywords, meta

def generate_article(title, topic):
    system_msg = """You are a Senior Investigative Tech Journalist. 
    STRICT GUIDELINES:
    1. FACTUALITY: Do NOT invent features for existing models (e.g., AlphaGo is for Go only). 
    2. SOURCES: Do NOT invent quotes from real people. Instead, use 'Industry analysts suggest' or 'Recent corporate reports indicate'.
    3. TONE: Serious, analytical, and objective. No 'mind-blowing' or 'revolutionary' clichés.
    4. NO HALLUCINATION: If you don't have current data on a specific private event, write a broader industry analysis.
    5. DATA-DRIVEN: Focus on trends, regulations, and architectural shifts in tech."""

    user_msg = f"""Write an 800-word authoritative report. 
    Headline: {title}
    Focus: {topic}
    Current Date: {today_date}
    Format: Use <h2> and <p> tags. Include one <blockquote> with a deep industry insight."""
    
    return groq_call(system_msg, user_msg)

# ✅ نظام الصور - تم تحسينه لتجنب "Hoodie Guy" والتركيز على الصور التقنية
def get_best_pexels_image(keywords, title):
    try:
        search_terms = keywords.replace(',', '').split() + title.split()
        # نركز على كلمات تقنية باش الصور يكونو "News-like"
        clean_terms = [w for w in search_terms if len(w) > 4 and w.lower() not in ["breaking", "news", "update"]]
        query = random.choice(clean_terms) if clean_terms else "technology"
        
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=20"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        
        if res.get("photos"):
            return random.choice(res["photos"])["src"]["large2x"]
        raise Exception("No photos found")
    except:
        hash_seed = abs(hash(title)) % 1000
        return f"https://picsum.photos/seed/{hash_seed}/1200/630"

def build_full_html(title, content, img, meta):
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "image": [img],
        "datePublished": today_iso,
        "author": {"@type": "Person", "name": "Mohamed Ismaili"}
    }
    
    return f"""
    <script type="application/ld+json">{json.dumps(schema)}</script>
    <div style="font-family: 'Georgia', serif; line-height: 1.8; color: #1a1a1a; max-width: 800px; margin: auto; padding: 20px;">
        <header style="border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 30px;">
            <h1 style="font-size: 36px; line-height: 1.2; font-weight: bold; margin-bottom: 10px;">{title}</h1>
            <p style="color: #555; font-size: 14px; font-weight: bold;">SMART FLOW NEWS CORRESPONDENT • {today_date}</p>
        </header>
        
        <img src="{img}" alt="{title}" style="width: 100%; height: auto; border-radius: 2px; margin-bottom: 30px;">
        
        <div style="font-size: 18px;">
            {content}
        </div>
        
        <div style="margin-top: 50px; padding: 25px; background: #f9f9f9; border-left: 4px solid #cc0000;">
            <strong style="font-size: 20px;">Mohamed Ismaili</strong><br>
            <span style="color: #666;">Senior Technology Analyst covering AI ethics, semiconductor markets, and digital infrastructure.</span>
        </div>
        
        <footer style="margin-top: 40px; text-align: center; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 20px;">
            © {current_year} Smart Flow Lab. All rights reserved. <br>
            Metadata Context: {meta}
        </footer>
    </div>
    """

def main():
    print("🚀 Running Professional News Engine...")
    chosen_topic = random.choice(TOPIC_ANGLES)
    title, keywords, meta = generate_meta(chosen_topic)
    
    if not title: return
    print(f"📰 Drafting: {title}")
    
    content = generate_article(title, chosen_topic)
    if not content: return
    
    img = get_best_pexels_image(keywords, title)
    full_html = build_full_html(title, content, img, meta)
    post_to_blogger_api(title, full_html)

if __name__ == "__main__":
    main()
