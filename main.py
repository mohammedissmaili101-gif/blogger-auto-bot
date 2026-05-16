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

# ══════════════════════════════════════════════
#  SECRETS
# ══════════════════════════════════════════════
GROQ_KEY      = os.environ.get("GROQ_API_KEY")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY")
NEWSAPI_KEY   = os.environ.get("NEWSAPI_KEY")
CLIENT_ID     = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

client       = Groq(api_key=GROQ_KEY)
today_iso    = datetime.datetime.now().isoformat()
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = datetime.date.today().year

# ══════════════════════════════════════════════
#  TECH DOMAINS — للتنويع في جلب الأخبار
# ══════════════════════════════════════════════
TECH_DOMAINS = [
    # AI & Machine Learning
    ("artificial intelligence breakthrough", "AI technology futuristic"),
    ("large language model AI", "neural network server"),
    ("AI regulation policy", "government technology policy"),
    ("machine learning enterprise", "enterprise AI data center"),
    ("generative AI tools", "AI creative technology"),
    # Semiconductors & Hardware
    ("semiconductor chip manufacturing", "silicon wafer factory"),
    ("GPU computing nvidia", "graphics processor technology"),
    ("chip shortage supply chain", "microchip supply chain"),
    ("RISC-V open hardware", "computer processor chip"),
    # Cybersecurity
    ("cybersecurity data breach", "cybersecurity network"),
    ("ransomware attack infrastructure", "hacker dark cyber"),
    ("zero trust security", "network security firewall"),
    ("quantum cryptography security", "encryption data protection"),
    # Cloud & Infrastructure
    ("cloud computing AWS Azure Google", "cloud data center"),
    ("edge computing IoT", "edge computing network"),
    ("data center energy consumption", "server farm energy"),
    ("serverless computing platform", "cloud infrastructure"),
    # Biotech & Health
    ("AI drug discovery", "laboratory research biotech"),
    ("digital health wearable", "health technology device"),
    ("CRISPR gene editing", "DNA laboratory science"),
    ("telemedicine remote healthcare", "doctor digital health"),
    # Energy & Climate
    ("battery storage renewable energy", "solar battery storage"),
    ("hydrogen fuel cell", "hydrogen energy plant"),
    ("nuclear fusion energy", "nuclear reactor energy"),
    ("carbon capture technology", "climate tech green"),
    # Finance & Fintech
    ("fintech digital payment", "mobile payment technology"),
    ("central bank digital currency", "digital currency blockchain"),
    ("open banking API", "banking technology fintech"),
    ("crypto regulation", "blockchain cryptocurrency"),
    # Space & Robotics
    ("space technology satellite", "rocket launch space"),
    ("robotics automation factory", "industrial robot arm"),
    ("drone delivery logistics", "drone technology aerial"),
    ("autonomous vehicle self-driving", "self-driving car sensor"),
    # Regulation & Policy
    ("big tech antitrust regulation", "government tech regulation"),
    ("data privacy GDPR", "data privacy law"),
    ("AI ethics regulation", "AI policy ethics"),
    ("digital trade policy", "international tech policy"),
    # Quantum & Emerging
    ("quantum computing breakthrough", "quantum computer lab"),
    ("augmented reality enterprise", "AR VR headset technology"),
    ("6G wireless network", "telecommunications network"),
    ("neuromorphic computing brain", "brain computer interface"),
]


# ══════════════════════════════════════════════
#  AI TOPIC GENERATOR — يولّد موضوعاً فريداً بالـ AI
# ══════════════════════════════════════════════
def generate_topic_from_news(used_titles, raw_articles):
    """
    يولّد موضوعاً + newsapi_query + image_queries
    بناءً على الأخبار الحقيقية والعناوين المستخدمة.
    """
    used_str = "\n".join(f"- {t}" for t in used_titles[-30:]) if used_titles else "None"
    news_str = "\n".join(
        f"- {a['title']} ({a['source']})" for a in raw_articles
    ) if raw_articles else "No headlines available"

    system_msg = (
        "You are an editorial director at a major technology publication. "
        "Your job is to identify the most newsworthy, unique technology angle "
        "worth covering today based on real headlines."
    )
    user_msg = (
        f"Today's real technology headlines:\n{news_str}\n\n"
        f"Already published topics (DO NOT repeat or closely paraphrase):\n{used_str}\n\n"
        "Based on the headlines above, identify ONE specific, compelling technology topic "
        "that is:\n"
        "1. Grounded in the real news provided\n"
        "2. NOT similar to any already-published topic\n"
        "3. Has enough depth for a 1200-word analytical article\n"
        "4. Interesting to tech executives, engineers, and policy professionals\n\n"
        "Output ONLY in this exact JSON format (no extra text, no markdown):\n"
        '{\n'
        '  "topic": "specific descriptive topic sentence (15-25 words)",\n'
        '  "newsapi_query": "3-5 word search query for NewsAPI",\n'
        '  "image_query": "3-4 word Pexels image search query"\n'
        '}'
    )

    raw = groq_call(system_msg, user_msg, max_tokens=300)
    if not raw:
        return None

    try:
        # تنظيف الـ JSON
        clean = re.sub(r'```json|```', '', raw).strip()
        data  = json.loads(clean)
        return {
            "topic":         data.get("topic", ""),
            "newsapi_query": data.get("newsapi_query", "technology innovation"),
            "image_queries": [data.get("image_query", "technology innovation")],
        }
    except Exception as e:
        print(f"⚠️ Topic JSON parse error: {e} | raw: {raw[:200]}")
        return None

# ══════════════════════════════════════════════
#  DEDUPLICATION — جلب العناوين مباشرة من Blogger API
# ══════════════════════════════════════════════

def get_published_titles_from_blogger():
    """
    جلب كل عناوين المقالات المنشورة مباشرة من Blogger API.
    لا يحتاج أي ملف محلي — المصدر الحقيقي هو Blogger نفسه.
    """
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
        blogs   = service.blogs().listByUser(userId='self').execute()
        blog_id = blogs['items'][0]['id']

        titles     = []
        page_token = None

        while True:
            params = {
                "blogId":    blog_id,
                "maxResults": 500,
                "fields":    "items(title),nextPageToken",
                "status":    "live",
            }
            if page_token:
                params["pageToken"] = page_token

            result     = service.posts().list(**params).execute()
            items      = result.get("items", [])
            titles    += [p["title"].strip() for p in items if "title" in p]
            page_token = result.get("nextPageToken")

            if not page_token:
                break

        print(f"📚 Fetched {len(titles)} existing post titles from Blogger")
        return titles

    except Exception as e:
        print(f"⚠️ Could not fetch titles from Blogger: {e}")
        return []


def fetch_trending_headlines():
    """جلب عناوين من عدة مجالات تقنية للتنويع."""
    if not NEWSAPI_KEY:
        return []

    # اختيار 3 domains عشوائية لتنويع الأخبار
    domains = random.sample(TECH_DOMAINS, min(3, len(TECH_DOMAINS)))
    all_articles = []

    for query, _ in domains:
        try:
            url = (
                "https://newsapi.org/v2/everything"
                f"?q={urllib.parse.quote(query)}"
                f"&language=en&sortBy=publishedAt&pageSize=5"
                f"&apiKey={NEWSAPI_KEY}"
            )
            res = requests.get(url, timeout=8).json()
            for a in res.get("articles", []):
                if a.get("title") and a.get("description"):
                    all_articles.append({
                        "title":       a["title"],
                        "source":      a.get("source", {}).get("name", "Unknown"),
                        "url":         a.get("url", ""),
                        "description": a.get("description", ""),
                        "published":   a.get("publishedAt", "")[:10],
                    })
        except Exception:
            continue

    print(f"📡 Fetched {len(all_articles)} trending headlines across domains")
    return all_articles


def get_next_topic(used_titles):
    """
    يولّد موضوعاً فريداً بالـ AI بناءً على أخبار اليوم الحقيقية.
    لا قائمة ثابتة — المواضيع لا نهائية.
    """
    # جلب أخبار متنوعة من عدة مجالات
    trending = fetch_trending_headlines()

    # محاولة توليد موضوع فريد — حتى 3 محاولات
    for attempt in range(1, 4):
        chosen = generate_topic_from_news(used_titles, trending)
        if chosen and chosen.get("topic"):
            print(f"✅ AI-generated topic (attempt {attempt}): {chosen['topic']}")
            # إضافة image_queries متعددة من TECH_DOMAINS كـ fallback
            if len(chosen["image_queries"]) < 2:
                extra = [img for _, img in random.sample(TECH_DOMAINS, 2)]
                chosen["image_queries"] += extra
            return chosen
        print(f"⚠️ Topic generation attempt {attempt} failed, retrying...")
        time.sleep(5)

    # Fallback: اختيار domain عشوائي إذا فشل التوليد
    print("⚠️ AI topic generation failed — using domain fallback")
    query, img = random.choice(TECH_DOMAINS)
    return {
        "topic":         f"Recent developments in {query}",
        "newsapi_query": query,
        "image_queries": [img],
    }


def is_title_duplicate(title, used_titles):
    """التحقق من أن العنوان لم يُستخدم مسبقاً."""
    used_lower = [t.lower().strip() for t in used_titles]
    return title.lower().strip() in used_lower

# ══════════════════════════════════════════════
#  NEWSAPI — جلب أخبار حقيقية مع فلتر متعدد المراحل
# ══════════════════════════════════════════════

# مصادر موثوقة في التقنية — الأولوية لها
TRUSTED_TECH_SOURCES = {
    "techcrunch", "wired", "the verge", "ars technica", "mit technology review",
    "ieee spectrum", "zdnet", "cnet", "venturebeat", "engadget", "gizmodo",
    "computerweekly", "computerworld", "infoworld", "networkworld",
    "siliconangle", "the information", "protocol", "axios", "reuters",
    "bloomberg", "financial times", "wall street journal", "forbes",
    "businessinsider", "cnbc", "bbc technology", "guardian technology",
    "decrypt", "coindesk", "cointelegraph", "techmonitor", "theregister",
    "pcmag", "tomshardware", "anandtech", "extremetech", "digitaltrends",
    "techradar", "macrumors", "9to5mac", "macdailynews", "arstechnica",
    "slashdot", "hackernews", "nature", "science", "newscientist",
    "thenextweb", "techmeme", "glassalmanac", "semafor", "platformer"
}

# مصادر وموضوعات يجب حذفها تماماً
BLOCKED_SOURCES = {
    "timeout", "time out", "road.cc", "cyclingnews", "velonews",
    "triathlete", "runnersworld", "menshealth", "womenshealth",
    "cosmopolitan", "vogue", "elle", "glamour", "allure",
    "foodnetwork", "epicurious", "bonappetit", "seriouseats",
    "espn", "bleacherreport", "sportingnews", "skysports",
    "tmz", "perezhilton", "people", "usmagazine", "eonline",
    "tripadvisor", "lonelyplanet", "travelandleisure",
    "horoscope", "astrology", "tarot",
}

BLOCKED_CONTENT_SIGNALS = [
    # رياضة غير تقنية
    "cycling saddle", "bum massage", "bike seat", "running shoe",
    "football match", "soccer game", "nba game", "nfl game",
    "tennis tournament", "golf tournament",
    # طعام وطبخ
    "recipe", "cooking", "baking", "restaurant review", "chef",
    "food festival", "wine tasting",
    # موضة وجمال
    "fashion week", "runway show", "makeup tutorial", "skincare",
    "celebrity style", "red carpet",
    # ترفيه وفن
    "box office", "movie review", "album review", "music video",
    "celebrity gossip", "reality show", "award show",
    # سفر
    "travel guide", "hotel review", "vacation", "tourist",
    # مالية غير ذات صلة
    "gold treasury", "gold coins", "forex trading", "real estate listing",
    "mortgage rate", "insurance policy",
    # قانوني غير ذات صلة  
    "arbitration case", "divorce", "personal injury",
    # متفرقات
    "horoscope", "astrology", "lottery", "gambling casino",
    "weight loss", "diet plan", "fitness routine",
]

# كلمات تقنية جوهرية — وجود أي منها يرفع احتمال القبول
CORE_TECH_SIGNALS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "chip", "semiconductor", "processor", "gpu", "cpu", "hardware",
    "software", "algorithm", "model", "neural", "data", "cloud",
    "cybersecurity", "encryption", "quantum", "blockchain", "crypto",
    "startup", "venture", "funding", "acquisition", "ipo",
    "regulation", "policy", "law", "court", "antitrust",
    "energy", "battery", "hydrogen", "renewable", "carbon",
    "biotech", "pharmaceutical", "drug", "clinical", "genomics",
    "robot", "autonomous", "drone", "satellite", "space",
    "network", "5g", "6g", "fiber", "bandwidth", "latency",
    "research", "study", "paper", "breakthrough", "discovery",
]


def _relevance_score(article, query_keywords, topic=""):
    """
    يحسب نقاط الصلة للمقال — نظام نقاط بدل True/False.
    يرجع رقم من 0 إلى 10.
    """
    title = article.get("title", "").lower()
    desc  = article.get("description", "").lower()
    text  = title + " " + desc
    source = article.get("source", "").lower()

    score = 0

    # +3 إذا المصدر موثوق تقنياً
    if any(ts in source for ts in TRUSTED_TECH_SOURCES):
        score += 3

    # كلمات الـ query
    stop = {"the", "and", "for", "with", "this", "that", "from", "have",
            "will", "are", "its", "has", "been", "into", "more", "also",
            "their", "they", "about", "which", "when", "where", "what"}
    q_words = [w for w in re.split(r"[\s\-]+", query_keywords.lower())
               if len(w) > 3 and w not in stop]

    # +1 لكل كلمة query في العنوان (وزن مضاعف)
    title_matches = sum(1 for w in q_words if w in title)
    score += title_matches * 2

    # +1 لكل كلمة query في الوصف
    desc_matches = sum(1 for w in q_words if w in desc)
    score += desc_matches

    # +1 لكل إشارة تقنية جوهرية
    tech_hits = sum(1 for sig in CORE_TECH_SIGNALS if sig in text)
    score += min(tech_hits, 3)  # حد أقصى 3 نقاط من هنا

    # topic إضافي
    if topic:
        t_words = [w for w in re.split(r"[\s\-]+", topic.lower())
                   if len(w) > 4 and w not in stop]
        topic_matches = sum(1 for w in t_words if w in text)
        score += min(topic_matches, 2)

    return score


def _is_blocked(article):
    """
    يتحقق إذا المقال يجب حذفه بسبب المصدر أو المحتوى.
    """
    title  = article.get("title", "").lower()
    desc   = article.get("description", "").lower()
    source = article.get("source", "").lower()
    text   = title + " " + desc

    # حذف إذا المصدر في القائمة السوداء
    if any(bs in source for bs in BLOCKED_SOURCES):
        return True

    # حذف إذا المحتوى يحتوي على إشارة محجوبة
    if any(sig in text for sig in BLOCKED_CONTENT_SIGNALS):
        return True

    return False


def fetch_real_news(query, topic="", max_articles=7):
    """
    جلب أخبار حقيقية مع فلتر متعدد المراحل:
    1. حذف المصادر والمحتوى المحجوب
    2. تسجيل نقاط الصلة لكل مقال
    3. ترتيب حسب النقاط وأخذ الأفضل
    """
    if not NEWSAPI_KEY:
        print("⚠️  NEWSAPI_KEY not set — skipping real news fetch")
        return []

    fetch_size = max_articles * 4  # نجلب 4× للتعويض عن الفلترة

    try:
        url = (
            "https://newsapi.org/v2/everything"
            f"?q={urllib.parse.quote(query)}"
            f"&language=en"
            f"&sortBy=publishedAt"
            f"&pageSize={min(fetch_size, 40)}"
            f"&apiKey={NEWSAPI_KEY}"
        )
        res = requests.get(url, timeout=10).json()

        raw_articles = []
        for a in res.get("articles", []):
            if a.get("title") and a.get("description"):
                raw_articles.append({
                    "title":       a["title"],
                    "source":      a.get("source", {}).get("name", "Unknown"),
                    "url":         a.get("url", ""),
                    "description": a.get("description", ""),
                    "published":   a.get("publishedAt", "")[:10],
                })

        # ── المرحلة 1: حذف المحجوب ──
        not_blocked = [a for a in raw_articles if not _is_blocked(a)]

        # ── المرحلة 2: تسجيل نقاط الصلة ──
        scored = []
        for a in not_blocked:
            s = _relevance_score(a, query, topic)
            if s >= 2:  # حد أدنى للقبول
                scored.append((s, a))

        # ── المرحلة 3: ترتيب حسب النقاط ──
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [a for _, a in scored[:max_articles]]

        # ── Fallback: إذا ما بقاش شي كافي ──
        if len(result) < 3:
            print("⚠️ Strict filter too aggressive — relaxing threshold")
            fallback = [(0, a) for a in not_blocked if a not in result]
            result += [a for _, a in fallback[:max_articles - len(result)]]

        blocked_count = len(raw_articles) - len(not_blocked)
        print(
            f"📡 News: {len(raw_articles)} fetched → "
            f"{blocked_count} blocked → {len(scored)} scored → "
            f"{len(result)} used"
        )
        return result

    except Exception as e:
        print(f"⚠️  NewsAPI error: {e}")
        return []


def format_news_for_prompt(articles):
    if not articles:
        return "No recent news available — rely on general knowledge."

    lines = ["RECENT NEWS CONTEXT (use these as factual references):"]
    for i, a in enumerate(articles, 1):
        lines.append(
            f"{i}. [{a['source']} — {a['published']}] {a['title']}\n"
            f"   Summary: {a['description']}\n"
            f"   URL: {a['url']}"
        )
    return "\n".join(lines)


def build_sources_html(articles):
    if not articles:
        return ""

    items = ""
    for a in articles:
        items += (
            f'<li style="margin-bottom: 8px;">'
            f'<a href="{a["url"]}" target="_blank" rel="noopener" '
            f'style="color: #cc0000; text-decoration: none;">'
            f'{a["title"]}</a> '
            f'<span style="color: #888; font-size: 13px;">— {a["source"]}, {a["published"]}</span>'
            f'</li>\n'
        )

    return f"""
<div style="margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 4px;">
    <h3 style="font-size: 16px; font-weight: bold; margin-bottom: 12px; color: #333;">
        📰 Sources &amp; References
    </h3>
    <ul style="list-style: disc; padding-left: 20px; margin: 0;">
        {items}
    </ul>
</div>
"""

# ══════════════════════════════════════════════
#  MARKDOWN → HTML
# ══════════════════════════════════════════════
def markdown_to_html(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
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


# أدوار محددة وموثوقة للـ blockquote
ANALYST_ROLES = [
    "Enterprise AI architect",
    "Semiconductor policy analyst",
    "Cloud infrastructure strategist",
    "Cybersecurity research lead",
    "Quantum computing engineer",
    "Digital health technology advisor",
    "Energy transition analyst",
    "Open-source ecosystem strategist",
    "Emerging markets tech analyst",
    "AI governance specialist",
    "Supply chain technology expert",
    "Fintech regulatory analyst",
]


def post_process_html(html):
    seen_h2 = []

    def dedup_h2(m):
        text = m.group(1).strip().lower()
        if text in seen_h2:
            return ''
        seen_h2.append(text)
        return m.group(0)

    html = re.sub(r'<h2[^>]*>(.*?)</h2>', dedup_h2, html, flags=re.IGNORECASE | re.DOTALL)
    role = random.choice(ANALYST_ROLES)
    html = re.sub(
        r'—\s*(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+[^<\n]{0,150}',
        f'— <em>{role}</em>',
        html
    )
    return html

# ══════════════════════════════════════════════
#  GROQ — نموذج أقوى + retry
# ══════════════════════════════════════════════
def groq_call(system_msg, user_msg, max_tokens=3500):
    MODEL = "llama-3.3-70b-versatile"

    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg}
                ],
                model=MODEL,
                temperature=0.45,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(12)
    return None

# ══════════════════════════════════════════════
#  META GENERATION
# ══════════════════════════════════════════════
def generate_meta(topic, used_titles=[]):
    used_str = "\n".join(f"- {t}" for t in used_titles[-20:]) if used_titles else "None"

    system_msg = (
        "You are a senior editor at MIT Technology Review or The Economist. "
        "You craft sharp, provocative headlines that make readers stop scrolling."
    )
    user_msg = (
        f"Generate SEO metadata for this topic: {topic}\n\n"
        f"BANNED titles — do NOT reuse or paraphrase:\n{used_str}\n\n"
        "TITLE RULES:\n"
        "- Max 65 characters\n"
        "- NEVER use prefixes like Update:, Report:, Analysis:, Breaking:\n"
        "- Sharp and specific — strong verbs, contrasts, or surprising angles\n"
        "- Style examples:\n"
        "  * Why Europe AI Rules Are Backfiring\n"
        "  * The Hidden Cost of Cheap Chips\n"
        "  * Quantum's Encryption Reckoning\n"
        "  * Open Source AI's Enterprise Moment\n"
        "  * The Battery Race Nobody Is Winning\n"
        "  * Chips, Power, and the AI Energy Crisis\n"
        "  * When Robots Replace the Factory Floor\n"
        "- Use surprising angles, contrasts, or provocative framings\n\n"
        "Output ONLY in this exact format:\n"
        "[TITLE] your headline here\n"
        "[KEYWORDS] keyword1, keyword2, keyword3\n"
        "[META] one compelling sentence under 155 chars"
    )
    raw = groq_call(system_msg, user_msg, max_tokens=300)
    if not raw:
        return None, None, None

    t = re.search(r"\[TITLE\]\s*(.*)",    raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)",     raw, re.I)

    title    = t.group(1).strip() if t else topic[:65]
    keywords = k.group(1).strip() if k else "Tech, News, Innovation"
    meta     = m.group(1).strip() if m else f"An in-depth analysis of {topic}."

    # إزالة أي prefix آلي تلقائياً
    import re as _re
    title = _re.sub(r"^(Update|Report|Analysis|Breaking|News):\s*", "", title, flags=_re.I).strip()

    return title, keywords, meta

# ══════════════════════════════════════════════
#  ARTICLE GENERATOR
# ══════════════════════════════════════════════
ARTICLE_STRUCTURES = [
    (
        "intro <p>(2 sentences hook) → "
        "Context <h2>+<p>(background + why it matters now) → "
        "Key Developments <h2>+<p>+<ul>(3-4 specific points from news) → "
        "Deep Analysis <h2>+<p>(cause-effect, implications, trade-offs) → "
        "Expert Perspective <blockquote> → "
        "What This Means <h2>+<p>(concrete impact on industry/users) → "
        "Conclusion <p>(forward-looking, no fluff)"
    ),
    (
        "hook <p>(start with a striking fact or contrast) → "
        "The Problem <h2>+<p>(define the challenge clearly) → "
        "Current Landscape <h2>+<p>+<ul>(who is doing what, from news) → "
        "Competing Forces <h2>+<p>(tensions, trade-offs, opposing views) → "
        "Analyst View <blockquote> → "
        "The Numbers <h2>+<p>(data points, market size, growth) → "
        "Outlook <p>(realistic assessment, not hype)"
    ),
    (
        "intro <p>(frame the debate or shift) → "
        "Historical Context <h2>+<p>(how we got here) → "
        "Breaking Point <h2>+<p>(what changed recently, from news) → "
        "Winners and Losers <h2>+<ul>(who benefits, who loses) → "
        "Industry Voice <blockquote> → "
        "Strategic Implications <h2>+<p>(what companies/governments should do) → "
        "Final Take <p>(author's analytical conclusion)"
    ),
    (
        "provocative hook <p>(challenge a common assumption) → "
        "The Case For <h2>+<p>+<ul>(strongest arguments, evidence) → "
        "The Case Against <h2>+<p>(counterarguments, risks) → "
        "Evidence from the Field <h2>+<p>(specific examples from news) → "
        "Expert Quote <blockquote> → "
        "Balancing Act <h2>+<p>(nuanced synthesis) → "
        "Verdict <p>(clear-eyed conclusion)"
    ),
]


def generate_article(title, topic, news_context):
    structure = random.choice(ARTICLE_STRUCTURES)

    system_msg = """You are a Senior Tech Analyst at Smart Flow Lab. You write deep, publication-quality industry analysis for an audience of executives, engineers, and policy professionals.

ABSOLUTE RULES:
1. HTML ONLY — use <h2>, <p>, <blockquote>, <ul>, <li>, <strong>, <em>. Zero Markdown.
2. LENGTH — 1100–1300 words of actual substantive content. This is non-negotiable.
3. NO REPETITION — each paragraph must introduce NEW information or analysis. Never restate what was already said.
4. GROUND IN REAL NEWS — reference provided sources naturally (e.g. "According to [Source], ..."). NEVER invent sources.
5. NO INVENTED PEOPLE — no fake names. Use: "analysts note...", "industry observers suggest...", "according to [Source]...".
6. NO FAKE STATISTICS — numbers must come from the provided news context. Otherwise: "estimates vary" or "industry reports suggest X to Y range".
7. DEPTH REQUIRED — go beyond describing events. Explain WHY it matters, WHAT the trade-offs are, WHO wins and loses, HOW it connects to broader trends.
8. BLOCKQUOTE — one sharp, specific industry voice (not generic):
   <blockquote style="border-left: 3px solid #cc0000; padding: 12px 20px; margin: 20px 0; background: #fafafa; font-style: italic; color: #444;">
   "..." — <em>[specific role, e.g. 'Semiconductor policy analyst' or 'Enterprise AI architect']</em></blockquote>
9. TONE — The Economist meets MIT Technology Review. Precise, analytical, no hype, no corporate speak.
10. STRONG OPENING — first sentence must hook the reader with a fact, paradox, or sharp observation. NOT a generic intro."""

    user_msg = (
        f"Write a deep industry analysis article. Target: 1100-1300 words.\n\n"
        f"Title: {title}\n"
        f"Topic: {topic}\n"
        f"Date: {today_date}\n\n"
        f"Structure to follow EXACTLY:\n{structure}\n\n"
        f"{news_context}\n\n"
        "QUALITY REQUIREMENTS:\n"
        "- Every section must add NEW analysis, not repeat previous points\n"
        "- At least 2-3 specific data points or concrete examples from the news context\n"
        "- Explain cause-effect relationships, not just describe events\n"
        "- Identify at least one non-obvious implication or tension\n"
        "- Pure HTML only, zero Markdown\n"
        "- The blockquote must be specific to this topic, not generic industry speak"
    )

    raw = groq_call(system_msg, user_msg)
    if not raw:
        return None

    cleaned = markdown_to_html(raw)
    cleaned = post_process_html(cleaned)
    return cleaned

# ══════════════════════════════════════════════
#  PEXELS IMAGE
# ══════════════════════════════════════════════
def get_best_pexels_image(image_queries):
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
            top_photos = res["photos"][:5]
            return random.choice(top_photos)["src"]["large2x"]

        raise Exception("No photos found")
    except Exception as e:
        print(f"⚠️ Pexels error: {e} — using fallback")
        hash_seed = abs(hash(str(image_queries))) % 1000
        return f"https://picsum.photos/seed/{hash_seed}/1200/630"

# ══════════════════════════════════════════════
#  HTML BUILDER
# ══════════════════════════════════════════════
def build_full_html(title, content, img, meta, sources_html, keywords):
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": meta,
        "keywords": keywords,
        "image": [img],
        "datePublished": today_iso,
        "dateModified":  today_iso,
        "author": {
            "@type": "Person",
            "name": "Mohamed Ismaili",
            "jobTitle": "Senior Technology Analyst",
            "worksFor": {
                "@type": "Organization",
                "name": "Smart Flow Lab"
            }
        },
        "publisher": {
            "@type": "Organization",
            "name": "Smart Flow Lab",
            "logo": {
                "@type": "ImageObject",
                "url": "https://owlab.blogspot.com/favicon.ico"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage"
        }
    }

    return f"""
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>

<div style="font-family: 'Georgia', serif; line-height: 1.85; color: #1a1a1a; max-width: 820px; margin: auto; padding: 24px 20px;">

    <!-- HEADER -->
    <header style="border-bottom: 3px solid #cc0000; padding-bottom: 18px; margin-bottom: 32px;">
        <p style="color: #cc0000; font-size: 12px; font-weight: bold; letter-spacing: 2px; 
                  text-transform: uppercase; margin-bottom: 10px;">
            Smart Flow Lab &nbsp;|&nbsp; Technology Analysis
        </p>
        <h1 style="font-size: 34px; line-height: 1.25; font-weight: bold; margin-bottom: 14px; color: #111;">
            {title}
        </h1>
        <p style="color: #555; font-size: 13px;">
            By <strong>Mohamed Ismaili</strong> &nbsp;&bull;&nbsp; {today_date} &nbsp;&bull;&nbsp;
            <em style="color: #888;">Senior Technology Analyst</em>
        </p>
        <p style="color: #666; font-size: 15px; font-style: italic; margin-top: 12px; 
                  border-left: 3px solid #ddd; padding-left: 12px;">
            {meta}
        </p>
    </header>

    <!-- MAIN IMAGE -->
    <figure style="margin: 0 0 32px 0;">
        <img src="{img}" alt="{title}" 
             style="width: 100%; height: auto; border-radius: 6px; display: block;">
        <figcaption style="font-size: 12px; color: #999; margin-top: 8px; text-align: center; 
                           font-style: italic;">
            {title} — Smart Flow Lab
        </figcaption>
    </figure>

    <!-- ARTICLE CONTENT -->
    <div style="font-size: 17px; color: #1a1a1a;">
        {content}
    </div>

    <!-- SOURCES SECTION -->
    {sources_html}

    <!-- AUTHOR BIO -->
    <div style="margin-top: 48px; padding: 24px; background: #f9f9f9; 
                border-left: 4px solid #cc0000; border-radius: 0 4px 4px 0;">
        <strong style="font-size: 18px; color: #111;">Mohamed Ismaili</strong><br>
        <span style="color: #555; font-size: 14px; line-height: 1.6;">
            Senior Technology Analyst at Smart Flow Lab — covering AI systems,
            semiconductor markets, cybersecurity, and digital infrastructure policy.
            Based in Morocco.
        </span>
    </div>

    <!-- DISCLAIMER -->
    <div style="margin-top: 24px; padding: 14px; background: #fff8f8; 
                border: 1px solid #f0dede; border-radius: 4px; font-size: 12px; color: #888;">
        <strong>Editorial Note:</strong> This analysis is based on publicly available industry 
        information and recent news sources. All opinions expressed are those of the author.
    </div>

    <!-- FOOTER -->
    <footer style="margin-top: 40px; text-align: center; font-size: 11px; color: #bbb;
                   border-top: 1px solid #eee; padding-top: 20px;">
        &copy; {current_year} Smart Flow Lab. All rights reserved. &nbsp;|&nbsp;
        <a href="https://owlab.blogspot.com" 
           style="color: #bbb; text-decoration: none;">owlab.blogspot.com</a>
    </footer>
</div>
"""

# ══════════════════════════════════════════════
#  BLOGGER PUBLISHER
# ══════════════════════════════════════════════
def post_to_blogger_api(title, html_content, keywords):
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
        blogs   = service.blogs().listByUser(userId='self').execute()
        blog_id = blogs['items'][0]['id']

        label_list = [k.strip() for k in keywords.split(',')][:3]
        label_list.append("News")

        body = {
            "kind":    "blogger#post",
            "title":   title,
            "content": html_content,
            "labels":  label_list
        }

        service.posts().insert(blogId=blog_id, body=body).execute()
        print(f"✅ Published: {title}")
    except Exception as e:
        print(f"❌ Blogger API Error: {e}")
        raise  # re-raise حتى لا يُسجَّل كمنشور ناجح

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════
def main():
    print("🚀 Smart Flow Lab Publisher v5 — Infinite Topics — starting...")

    # 1. جلب العناوين الموجودة مباشرة من Blogger — لا ملفات محلية
    used_titles = get_published_titles_from_blogger()

    # 2. AI يولّد موضوعاً فريداً بناءً على أخبار اليوم
    chosen        = get_next_topic(used_titles)
    topic         = chosen["topic"]
    image_queries = chosen["image_queries"]
    newsapi_query = chosen["newsapi_query"]

    # 3. جلب أخبار متعمقة للموضوع المختار مع فلتر صارم
    print(f"📡 Fetching deep news for: {newsapi_query}")
    articles     = fetch_real_news(newsapi_query, topic=topic, max_articles=7)
    news_context = format_news_for_prompt(articles)
    sources_html = build_sources_html(articles)

    # 4. توليد metadata — يمرر العناوين الموجودة لتجنب التشابه
    title, keywords, meta = generate_meta(topic, used_titles)
    if not title:
        print("❌ Metadata generation failed. Stopping.")
        return

    # 5. التحقق من عدم تكرار العنوان — retry مرتين إذا مكرر
    attempts = 0
    while is_title_duplicate(title, used_titles) and attempts < 2:
        attempts += 1
        print(f"⚠️ Duplicate title: '{title}' — retry {attempts}...")
        title, keywords, meta = generate_meta(topic, used_titles)

    if is_title_duplicate(title, used_titles):
        print("❌ Could not generate unique title after retries. Stopping.")
        return

    # ── تنظيف نهائي مضمون — حذف أي prefix آلي قبل النشر ──
    title = re.sub(
        r"^(Update|Report|Analysis|Breaking|News|Review|Overview)[\s:.\-]+",
        "", title, flags=re.I
    ).strip()
    if title:
        title = title[0].upper() + title[1:]

    print(f"📰 Final title: {title}")

    # 6. توليد المقال
    content = generate_article(title, topic, news_context)
    if not content:
        print("❌ Article generation failed. Stopping.")
        return

    # 7. الصورة
    img = get_best_pexels_image(image_queries)

    # 8. بناء HTML الكامل
    full_html = build_full_html(title, content, img, meta, sources_html, keywords)

    # 9. النشر
    post_to_blogger_api(title, full_html, keywords)
    print("🎉 Done!")


if __name__ == "__main__":
    main()
