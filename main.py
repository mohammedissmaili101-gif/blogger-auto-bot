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
            "labels": ["Tech News", "AI Updates", "Innovation"]
        }
        
        service.posts().insert(blogId=blog_id, body=body).execute()
        print(f"✅ Article Published: {title}")
    except Exception as e:
        print(f"❌ Blogger API Error: {e}")

# ── Improved Topic Rotation ────────────────────────
TOPIC_ANGLES = [
    "latest AI models and LLM benchmarks",
    "real-world AI applications in modern medicine",
    "semiconductor industry news and NVIDIA market performance",
    "cybersecurity threats and AI-driven defense mechanisms",
    "the evolution of humanoid robots in manufacturing",
    "big tech regulatory challenges and antitrust lawsuits"
]

def groq_call(prompt, max_tokens=1500):
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "You are a professional tech journalist. Use real company names. No future dates. Factual news tone."},
                          {"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(10)
    return None

def generate_meta(topic, modifier):
    prompt = f"Topic: {topic}. {modifier}. Generate: [TITLE] (max 65 chars), [KEYWORDS], [META] (max 160 chars)."
    raw = groq_call(prompt, max_tokens=300)
    
    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)", raw, re.I)
    
    title = t.group(1).strip() if t else f"Tech Update: {topic.title()}"
    keywords = k.group(1).strip() if k else "AI, Tech, News"
    meta = m.group(1).strip() if m else f"Analysis on {topic}."
    
    return title, keywords, meta

def generate_article(title, topic):
    prompt = f"Write a 800-word journalistic report about: {title}. Context: {topic}. Use current date: {today_date}. Format with <h2> and <p> and <blockquote>."
    return groq_call(prompt, max_tokens=2000)

# ✅ إصلاح مشكلة تكرار الصور
def get_best_pexels_image(keywords, title):
    try:
        # ندمج الكلمات وننقيها
        words = re.sub(r'[^\w\s]', '', keywords + " " + title).split()
        # نختار كلمة عشوائية "ذات قيمة" للبحث (تجنب كلمات مثل a, the, in)
        important_words = [w for w in words if len(w) > 4]
        search_query = random.choice(important_words) if important_words else "technology"
        
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(search_query)}&per_page=15"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        
        if res.get("photos"):
            return random.choice(res["photos"])["src"]["large2x"]
        
        raise Exception("No photos found")
    except:
        # fallback ذكي يعتمد على العنوان لضمان الاختلاف
        seed = "".join(filter(str.isdigit, str(hash(title))))[:5]
        return f"https://picsum.photos/seed/{seed}/1200/630"

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
    <div style="font-family: sans-serif; line-height: 1.6; color: #222; max-width: 800px; margin: auto;">
        <header style="border-bottom: 3px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
            <h1 style="font-size: 32px;">{title}</h1>
            <p style="color: #666;">By Smart Flow News • {today_date}</p>
        </header>
        <img src="{img}" style="width: 100%; border-radius: 4px; margin-bottom: 20px;">
        <div style="font-size: 18px;">{content}</div>
        <div style="background: #f9f9f9; padding: 15px; margin-top: 30px; border-left: 5px solid #0056b3;">
            <strong>Author: Mohamed Ismaili</strong><br>Tech analyst at Smart Flow Lab.
        </div>
    </div>
    """

def main():
    print("🚀 News Engine Started...")
    chosen_topic = random.choice(TOPIC_ANGLES)
    title, keywords, meta = generate_meta(chosen_topic, "Factual news update")
    if not title: return
    
    print(f"📰 Writing: {title}")
    content = generate_article(title, chosen_topic)
    if not content: return
    
    img = get_best_pexels_image(keywords, title)
    full_html = build_full_html(title, content, img, meta)
    post_to_blogger_api(title, full_html)

if __name__ == "__main__":
    main()
