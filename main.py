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

# ── Secrets (باقية كيفما هي) ─────────────────────────────
GROQ_KEY      = os.environ.get("GROQ_API_KEY")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY")
CLIENT_ID     = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

client       = Groq(api_key=GROQ_KEY)
today_iso    = datetime.datetime.now().isoformat() # للـ Schema
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
            "labels": ["Tech News", "AI Updates", "Innovation"] # زدنا تصنيفات أدق
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
                messages=[{"role": "system", "content": "You are a professional tech journalist. Use real company names (Google, Apple, OpenAI, etc.). Never use future dates. Write in a factual, news-driven tone."},
                          {"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.7, # نقصنا الـ temperature باش يكون "واقعي" أكتر
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(10)
    return None

def generate_meta(topic, modifier):
    # برومبت صارم باش ميخرجش ليك "In 2026"
    prompt = f"Topic: {topic}. {modifier}. Generate: [TITLE] (max 65 chars), [KEYWORDS], [META] (max 160 chars). Ensure the title is factual and current for {current_year}."
    raw = groq_call(prompt, max_tokens=300)
    
    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)", raw, re.I)
    
    backup_title = f"New Update in {topic.title()}: {current_year} Analysis"
    
    title = t.group(1).strip() if t else backup_title
    keywords = k.group(1).strip() if k else "AI, Tech, News"
    meta = m.group(1).strip() if m else f"Latest professional analysis on {topic}."
    
    return title, keywords, meta

def generate_article(title, topic):
    # طلبنا من الـ AI يستخدم هيكل الهرم المقلوب (Inverted Pyramid) ديال الصحافة
    prompt = f"""
    Write a 800-word journalistic news report about: {title}.
    Context: {topic}.
    Rules:
    1. Use 'Inverted Pyramid' style (most important info first).
    2. Include real industry names and potential expert insights.
    3. NO FUTURE DATES. Use current date: {today_date}.
    4. Format with ONLY <h2> and <p> and <blockquote>.
    5. Ending with a 'Conclusion' or 'Future Outlook' section.
    """
    return groq_call(prompt, max_tokens=2000)

def get_best_pexels_image(keywords, title):
    try:
        # تنقية الكلمات المفتاحية للبحث
        clean_query = keywords.split(',')[0] if ',' in keywords else title.split()[0]
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(clean_query)}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        return res["photos"][0]["src"]["large2x"]
    except:
        return f"https://picsum.photos/1200/630?random={random.randint(1, 1000)}"

def build_full_html(title, content, img, meta):
    # إضافة Schema Markup (مهم جداً لـ Google News)
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "image": [img],
        "datePublished": today_iso,
        "author": {
            "@type": "Person",
            "name": "Mohamed Ismaili",
            "url": "https://yourblogurl.com" 
        }
    }
    
    return f"""
    <script type="application/ld+json">
    {json.dumps(schema)}
    </script>
    
    <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #222; max-width: 800px; margin: auto;">
        <header style="margin-bottom: 30px; border-bottom: 3px solid #000; padding-bottom: 10px;">
            <h1 style="font-size: 32px; font-weight: 800; line-height: 1.2;">{title}</h1>
            <p style="color: #555; font-style: italic;">By Smart Flow News Team • Updated {today_date}</p>
        </header>
        
        <img src="{img}" alt="{title}" style="width: 100%; height: auto; border-radius: 4px; margin-bottom: 20px;">
        
        <div class="article-content" style="font-size: 18px; color: #333;">
            {content}
        </div>
        
        <div style="background: #f4f4f4; padding: 20px; border-radius: 10px; margin-top: 40px; border-left: 5px solid #0056b3;">
            <h4 style="margin-top: 0;">About the Author</h4>
            <p style="font-size: 14px; margin-bottom: 0;"><strong>Mohamed Ismaili</strong> is a tech analyst covering the intersection of AI and business. With years of experience in software engineering, he provides deep insights into the Silicon Valley ecosystem.</p>
        </div>
        
        <footer style="margin-top: 50px; text-align: center; border-top: 1px solid #ddd; padding-top: 20px; color: #888; font-size: 12px;">
            © {current_year} Smart Flow Lab. All Rights Reserved. <br>
            Tags: {meta}
        </footer>
    </div>
    """

def main():
    print("🚀 News Engine Started...")
    
    chosen_topic = random.choice(TOPIC_ANGLES)
    random_modifier = random.choice([
        "Focus on market data and financial impact",
        "Analyze the ethical implications for users",
        "Compare this update with historical tech shifts",
        "Report on the technical specifications and benchmarks"
    ])

    title, keywords, meta = generate_meta(chosen_topic, random_modifier)
    if not title: return
    
    print(f"📰 Writing: {title}")
    content = generate_article(title, chosen_topic)
    if not content: return
    
    img = get_best_pexels_image(keywords, title)
    full_html = build_full_html(title, content, img, meta)

    post_to_blogger_api(title, full_html)

if __name__ == "__main__":
    main()
