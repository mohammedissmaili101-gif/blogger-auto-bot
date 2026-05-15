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
            "labels": ["News"] # تم التعديل هنا ليكون News فقط
        }
        
        service.posts().insert(blogId=blog_id, body=body).execute()
        print(f"✅ Article Published: {title}")
    except Exception as e:
        print(f"❌ Blogger API Error: {e}")

# ── Topics for High Traffic ────────────────────────
TOPIC_ANGLES = [
    "major artificial intelligence breakthroughs this week",
    "the future of global economy and tech stock market",
    "revolutionary medical technologies saving lives",
    "cybersecurity alerts and data protection updates",
    "space exploration and new satellite discoveries",
    "renewable energy innovations and climate tech"
]

def groq_call(prompt, max_tokens=1500):
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "You are an elite news editor. Write high-impact, factual headlines and investigative reports. Use real names. NO future dates."},
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
    prompt = f"Topic: {topic}. {modifier}. Generate: [TITLE] (viral headline, max 65 chars), [KEYWORDS] (3 specific words), [META] (compelling summary)."
    raw = groq_call(prompt, max_tokens=300)
    
    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)", raw, re.I)
    
    title = t.group(1).strip() if t else f"Breaking News: {topic.title()}"
    keywords = k.group(1).strip() if k else "News, Tech, Future"
    meta = m.group(1).strip() if m else f"Latest exclusive report on {topic}."
    
    return title, keywords, meta

def generate_article(title, topic):
    prompt = f"Write a professional 800-word news article about: {title}. Focus on {topic}. Include expert-style analysis. Date: {today_date}. Format with <h2> and <p> only."
    return groq_call(prompt, max_tokens=2000)

# ✅ نظام الصور المتطور لضمان التنوع والجودة (Viral Quality)
def get_best_pexels_image(keywords, title):
    try:
        # خلط الكلمات لاستخراج أفضل نتيجة بحث ممكنة
        search_terms = keywords.replace(',', '').split() + title.split()
        # استبعاد الكلمات القصيرة وغير المفيدة
        clean_terms = [w for w in search_terms if len(w) > 4]
        
        # محاولة البحث بكلمتين عشوائيتين لزيادة الدقة
        query = " ".join(random.sample(clean_terms, min(2, len(clean_terms)))) if clean_terms else "innovation"
        
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=20"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        
        if res.get("photos"):
            # اختيار صورة عشوائية من أفضل 20 نتيجة لضمان عدم التكرار
            return random.choice(res["photos"])["src"]["large2x"]
        
        raise Exception("No specific photos found")
    except:
        # Fallback احترافي: صور تقنية عالية الجودة متغيرة بناءً على العنوان
        hash_seed = abs(hash(title)) % 10000
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
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.8; color: #111; max-width: 800px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 8px;">
        <header style="border-bottom: 4px solid #cc0000; padding-bottom: 15px; margin-bottom: 25px;">
            <h1 style="font-size: 38px; line-height: 1.1; font-weight: bold; letter-spacing: -1px;">{title}</h1>
            <p style="color: #666; text-transform: uppercase; font-size: 13px; font-weight: bold;">Exclusive Report • {today_date} • By Smart Flow Editor</p>
        </header>
        
        <figure style="margin: 0 0 25px 0;">
            <img src="{img}" alt="{title}" style="width: 100%; height: auto; border-radius: 5px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <figcaption style="font-size: 12px; color: #888; margin-top: 8px; text-align: right;">Visual representation of today's top story.</figcaption>
        </figure>

        <div style="font-size: 19px; color: #333; text-align: justify;">
            {content}
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #fdfdfd; border-top: 1px solid #ddd; display: flex; align-items: center;">
            <div style="width: 60px; height: 60px; background: #cc0000; color: #fff; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 24px; margin-right: 15px;">MI</div>
            <div>
                <strong style="font-size: 18px;">Mohamed Ismaili</strong><br>
                <span style="color: #777; font-size: 14px;">Senior Tech Correspondent at Smart Flow Lab.</span>
            </div>
        </div>
        
        <footer style="margin-top: 30px; text-align: center; font-size: 12px; color: #aaa; border-top: 1px dotted #ccc; padding-top: 20px;">
            © {current_year} Smart Flow Lab News - All Rights Reserved.<br>
            Source Analysis: {meta}
        </footer>
    </div>
    """

def main():
    print("🚀 News Engine Active...")
    chosen_topic = random.choice(TOPIC_ANGLES)
    # طلب عنوان بصيغة الخبر العاجل (Breaking)
    title, keywords, meta = generate_meta(chosen_topic, "Make it sound like a viral breaking news headline")
    
    if not title: return
    print(f"📰 Generating Viral Content: {title}")
    
    content = generate_article(title, chosen_topic)
    if not content: return
    
    img = get_best_pexels_image(keywords, title)
    full_html = build_full_html(title, content, img, meta)
    
    post_to_blogger_api(title, full_html)

if __name__ == "__main__":
    main()
