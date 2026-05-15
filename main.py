import os
import re
import datetime
import urllib.parse
import requests
import random
import time
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
# تصحيح الفراغ في التاريخ لضمان مظهر احترافي
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

# ── Topic Rotation System ────────────────────────
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year}",
    f"a BREAKTHROUGH scientific study about productivity using technology in {current_year}",
    f"a revolutionary AI-powered tool for students in {current_year}",
    f"a major Silicon Valley corporate shakeup happening RIGHT NOW in {current_year}",
    f"the fierce battle between OpenAI vs Google vs Meta in {current_year}",
    f"a cutting-edge AI application in healthcare that just got massive funding in {current_year}",
    f"how a newly released AI coding tool in {current_year} is transforming software engineering",
    f"a viral AI use case that regular people are adopting RIGHT NOW in {current_year}",
]

def groq_call(prompt, max_tokens=1500):
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.8,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(15) # وقت راحة أطول بين المحاولات
    return None

def generate_meta(topic, modifier):
    prompt = f"Topic: {topic}\nModifier: {modifier}\nGenerate ONLY: [TITLE] (max 65 chars), [KEYWORDS], [META] (max 160 chars)"
    raw = groq_call(prompt, max_tokens=200)
    
    # محاولة استخراج البيانات
    t = re.search(r"\[TITLE\]\s*(.*)", raw, re.I) if raw else None
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I) if raw else None
    m = re.search(r"\[META\]\s*(.*)", raw, re.I) if raw else None
    
    # 🛡️ نظام الخطة البديلة (Backup) لضمان عدم التكرار
    # إذا فشل AI، ننشئ عنواناً من اسم الموضوع المختار
    safe_topic_name = topic.split("in")[0].strip().title()
    backup_title = f"{safe_topic_name}: {current_year} Tech Update"
    
    title = t.group(1).strip() if t else backup_title
    keywords = k.group(1).strip() if k else "AI, Technology, Innovation"
    meta = m.group(1).strip() if m else f"Latest insights on {topic}."
    
    return title, keywords, meta

def generate_article(title, topic):
    prompt = f"Title: {title}\nTopic: {topic}\nWrite a long investigative article (800 words). Use ONLY <p>, <h2>, <blockquote>, <strong>. No markdown."
    return groq_call(prompt, max_tokens=1800)

def get_best_pexels_image(keywords, title):
    try:
        # ندمج الكلمات المفتاحية مع أول كلمتين من العنوان لضمان اختلاف الصورة
        search_term = f"{keywords} {title.split()[0]}"
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(search_term)}&per_page=1"
        res = requests.get(url, headers={"Authorization": PEXELS_KEY}, timeout=10).json()
        return res["photos"][0]["src"]["large2x"]
    except:
        # إذا فشل Pexels، نجلب صورة عشوائية تماماً من المصدر الاحتياطي
        return f"https://picsum.photos/1200/630?random={random.randint(1, 1000)}"

def build_full_html(title, content, img, meta):
    return f"""
    <div style="font-family: 'Georgia', serif; line-height: 1.8; color: #1a1a1a; max-width: 800px; margin: auto;">
        <div style="text-align: center; border-bottom: 2px solid #333; padding: 20px;">
            <h1 style="font-size: 36px; margin-bottom: 10px;">{title}</h1>
            <p style="color: #666;">Smart Flow Lab Exclusive • {today_date}</p>
        </div>
        <img src="{img}" style="width: 100%; border-radius: 8px; margin: 30px 0;">
        <div style="font-size: 19px;">{content}</div>
        <hr style="margin: 50px 0; border: 0; border-top: 1px solid #eee;">
        <footer style="text-align: center; color: #999; font-size: 12px;">
            © {current_year} Smart Flow Lab. Meta: {meta}
        </footer>
    </div>
    """

def main():
    print("🚀 Starting Engine (API Mode)...")
    
    # اختيار الموضوع واللمسة بشكل عشوائي في كل مرة يعمل فيها السكريبت
    chosen_topic = random.choice(TOPIC_ANGLES)
    random_modifier = random.choice([
        "Focus on a hidden scandal or controversy.",
        "Highlight the extreme financial implications.",
        "Make the title sound like a high-stakes thriller headline.",
        "Focus on the human impact and societal consequences.",
    ])

    title, keywords, meta = generate_meta(chosen_topic, random_modifier)
    if not title: return
    
    print(f"📰 Generating Content for: {title}")
    content = generate_article(title, chosen_topic)
    if not content: return
    
    # نمرر العنوان لجلب صورة متوافقة معه
    img = get_best_pexels_image(keywords, title)
    full_html = build_full_html(title, content, img, meta)

    post_to_blogger_api(title, full_html)
    
    # ⏳ وقت راحة اختياري إذا كنت تشغل السكريبت في حلقة تكرارية (Loop)
    # time.sleep(30) 

if __name__ == "__main__":
    main()
