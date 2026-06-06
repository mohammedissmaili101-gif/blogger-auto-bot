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
#  TOPICS
# ══════════════════════════════════════════════
TOPIC_ANGLES = [
    {
        "topic": "Latest developments in Generative AI architectures and LLM training costs",
        "newsapi_query": "generative AI LLM training",
        "image_queries": ["artificial intelligence server room", "neural network computing", "data center GPU cluster"]
    },
    {
        "topic": "Global semiconductor supply chain shifts and geopolitical impact on tech",
        "newsapi_query": "semiconductor supply chain geopolitics",
        "image_queries": ["semiconductor chip manufacturing", "silicon wafer factory", "microchip production"]
    },
    {
        "topic": "Emerging cybersecurity protocols for protecting decentralized financial data",
        "newsapi_query": "cybersecurity blockchain financial data",
        "image_queries": ["cybersecurity network protection", "blockchain technology digital", "data encryption security"]
    },
    {
        "topic": "Advancements in biotechnology and AI-driven drug discovery efficiency",
        "newsapi_query": "AI drug discovery biotechnology 2025",
        "image_queries": ["biotechnology laboratory research", "drug discovery microscope", "pharmaceutical AI research"]
    },
    {
        "topic": "Sustainable energy tech: Next-generation battery storage and hydrogen power",
        "newsapi_query": "battery storage hydrogen energy technology",
        "image_queries": ["hydrogen fuel cell technology", "battery storage renewable energy", "sustainable energy grid"]
    },
    {
        "topic": "Big Tech antitrust regulations: Europe vs. Silicon Valley's legal landscape",
        "newsapi_query": "big tech antitrust regulation Europe",
        "image_queries": ["tech regulation government policy", "silicon valley headquarters", "european union technology law"]
    },
    {
        "topic": "The rise of edge computing and its impact on real-time AI applications",
        "newsapi_query": "edge computing AI real-time applications",
        "image_queries": ["edge computing network", "IoT devices smart city", "real-time data processing"]
    },
    {
        "topic": "Quantum computing milestones and the threat to modern encryption standards",
        "newsapi_query": "quantum computing encryption breakthrough",
        "image_queries": ["quantum computer laboratory", "quantum processor chip", "quantum computing research"]
    },
    {
        "topic": "Open-source AI models vs proprietary systems: the enterprise dilemma",
        "newsapi_query": "open source AI models enterprise",
        "image_queries": ["open source software development", "enterprise AI server", "software collaboration code"]
    },
    {
        "topic": "Digital health transformation: AI diagnostics and remote patient monitoring",
        "newsapi_query": "AI diagnostics digital health remote monitoring",
        "image_queries": ["digital health technology", "AI medical diagnosis", "remote patient monitoring device"]
    },
    {
        "topic": "Autonomous vehicles and the regulatory road ahead in 2025",
        "newsapi_query": "autonomous vehicles regulation 2025",
        "image_queries": ["self-driving car technology", "autonomous vehicle sensor", "electric vehicle future"]
    },
    {
        "topic": "The economics of cloud computing: hyperscalers and the cost efficiency race",
        "newsapi_query": "cloud computing hyperscaler cost efficiency",
        "image_queries": ["cloud computing data center", "hyperscale server farm", "cloud infrastructure network"]
    },
]

# ══════════════════════════════════════════════
#  DEDUPLICATION
# ══════════════════════════════════════════════
HISTORY_FILE = "published_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"topics": [], "titles": []}


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_next_topic(history):
    used_topics = set(history.get("topics", []))
    available   = [t for t in TOPIC_ANGLES if t["topic"] not in used_topics]
    if not available:
        print("🔄 All topics used — starting new cycle")
        history["topics"] = []
        available = TOPIC_ANGLES
    chosen = random.choice(available)
    print(f"✅ Selected topic: {chosen['topic']}")
    return chosen


def is_title_duplicate(title, history):
    used_titles = [t.lower().strip() for t in history.get("titles", [])]
    return title.lower().strip() in used_titles


def record_published(history, topic, title):
    history.setdefault("topics", []).append(topic)
    history.setdefault("titles", []).append(title)
    history["titles"] = history["titles"][-100:]
    save_history(history)

# ══════════════════════════════════════════════
#  NEWSAPI
# ══════════════════════════════════════════════
def fetch_real_news(query, max_articles=5):
    if not NEWSAPI_KEY:
        print("⚠️  NEWSAPI_KEY not set — skipping real news fetch")
        return []
    try:
        url = (
            "https://newsapi.org/v2/everything"
            f"?q={urllib.parse.quote(query)}"
            f"&language=en"
            f"&sortBy=publishedAt"
            f"&pageSize={max_articles}"
            f"&apiKey={NEWSAPI_KEY}"
        )
        res = requests.get(url, timeout=10).json()
        articles = []
        for a in res.get("articles", []):
            if a.get("title") and a.get("description"):
                articles.append({
                    "title":       a["title"],
                    "source":      a.get("source", {}).get("name", "Unknown"),
                    "url":         a.get("url", ""),
                    "description": a.get("description", ""),
                    "published":   a.get("publishedAt", "")[:10]
                })
        print(f"📡 Fetched {len(articles)} real news articles for: {query}")
        return articles
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


def post_process_html(html):
    seen_h2 = []

    def dedup_h2(m):
        text = m.group(1).strip().lower()
        if text in seen_h2:
            return ''
        seen_h2.append(text)
        return m.group(0)

    html = re.sub(r'<h2[^>]*>(.*?)</h2>', dedup_h2, html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(
        r'—\s*(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+[^<\n]{0,150}',
        '— <em>Senior industry analyst</em>',
        html
    )
    return html

# ══════════════════════════════════════════════
#  GROQ
# ══════════════════════════════════════════════
def groq_call(system_msg, user_msg, max_tokens=2500, temp=0.45):
    MODEL = "llama-3.3-70b-versatile"
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg}
                ],
                model=MODEL,
                temperature=temp,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            time.sleep(12)
    return None

# ══════════════════════════════════════════════
#  META GENERATION — عناوين صحفية جذابة
# ══════════════════════════════════════════════
def generate_meta(topic, used_titles, temp=0.45):
    used_str = "\n".join(f"- {t}" for t in used_titles[-20:]) if used_titles else "None"

    system_msg = (
        "You are a world-class headline editor at Reuters and The Economist. "
        "You write magnetic, precise, news-wire quality headlines that rank on Google News. "
        "You must respond ONLY with a valid JSON object — no markdown, no preamble, parseable by json.loads()."
    )

    avoid_extra = ""
    if temp > 0.5:
        avoid_extra = " CRITICAL: Radically different angle and wording. No overlap with previous titles."

    user_msg = (
        f"Write news metadata for this topic: {topic}.{avoid_extra}\n\n"
        f"BANNED — do NOT reuse any of these titles:\n{used_str}\n\n"

        "HEADLINE RULES:\n"
        "- Must be between 55–70 characters\n"
        "- Use news-wire formats: 'X Does Y as Z', 'Why X Is Reshaping Y', 'The X Behind Y's Rise', "
        "'How X Is Quietly Changing Y', 'X Faces Y: What It Means for Z'\n"
        "- Include a power word: Reshaping / Quietly / Quietly / Surge / Faces / Behind / Quietly / Crisis / Race\n"
        "- Be specific — name the real technology, market, or policy under discussion\n"
        "- NEVER start with: 'The Rise of', 'Latest', 'Update', 'New', 'Top'\n\n"

        "Respond ONLY with this JSON:\n"
        "{\n"
        '  "title": "Your headline here",\n'
        '  "keywords": "3 comma-separated SEO terms",\n'
        '  "meta": "One compelling summary sentence, 120–155 characters"\n'
        "}"
    )

    raw = groq_call(system_msg, user_msg, max_tokens=300, temp=temp)
    if not raw:
        return None, None, None

    try:
        clean_json = re.search(r"\{.*\}", raw, re.DOTALL)
        if clean_json:
            data = json.loads(clean_json.group(0))
            title    = data.get("title", "").strip()
            keywords = data.get("keywords", "").strip()
            meta     = data.get("meta", "").strip()
            if title:
                return title, keywords, meta
    except Exception as e:
        print(f"⚠️ JSON parsing failed, trying fallback regex: {e}")

    t = re.search(r'"title":\s*"(.*?)"', raw, re.I)
    k = re.search(r'"keywords":\s*"(.*?)"', raw, re.I)
    m = re.search(r'"meta":\s*"(.*?)"', raw, re.I)

    title    = t.group(1).strip() if t else f"Analysis on {topic}"
    keywords = k.group(1).strip() if k else "Tech, News, Innovation"
    meta     = m.group(1).strip() if m else f"Latest analysis on {topic}."
    return title, keywords, meta

# ══════════════════════════════════════════════
#  PERSONAL ANALYSIS PARAGRAPH
# ══════════════════════════════════════════════
def generate_personal_analysis(title, topic, news_context):
    """
    يولد فقرة تحليل شخصي موقعة باسم Mohamed Ismaili.
    تعكس رأيه كمحلل تقني — ليست ملخصاً بل موقف محدد.
    """
    system_msg = (
        "You are Mohamed Ismaili, a Senior Technology Analyst at Smart Flow Lab based in Morocco. "
        "You write sharp, opinionated first-person analysis — like a columnist at The Economist or MIT Technology Review. "
        "Your voice is confident, analytical, and contrarian when warranted. "
        "You cite real data points when available. You challenge consensus when you see evidence for it. "
        "Write in pure HTML only. No markdown."
    )

    user_msg = (
        f"Write a personal analysis paragraph (180–230 words) about this article.\n\n"
        f"Article title: {title}\n"
        f"Topic: {topic}\n\n"
        f"{news_context}\n\n"
        "Requirements:\n"
        "- Start with: <h2 style=\"font-size: 22px; font-weight: bold; margin: 36px 0 14px; color: #111;\">My Take: [short subheading]</h2>\n"
        "- Then write ONE <p> paragraph in first person (I, my, in my view)\n"
        "- Express a specific, defensible opinion about where this technology/market is heading\n"
        "- Reference at least one real data point or trend from the news context\n"
        "- Challenge at least one mainstream assumption if the evidence supports it\n"
        "- End with a forward-looking sentence about what to watch in the next 6–12 months\n"
        "- Tone: analytical, not promotional. Think, not hype.\n"
        "- Pure HTML only. No markdown."
    )

    raw = groq_call(system_msg, user_msg, max_tokens=500, temp=0.55)
    if not raw:
        return ""
    cleaned = markdown_to_html(raw)
    return cleaned

# ══════════════════════════════════════════════
#  ARTICLE GENERATOR — جودة صحفية احترافية
# ══════════════════════════════════════════════
ARTICLE_STRUCTURES = [
    "intro_paragraph → Background [h2] → Current Developments [h2 + p + ul] → Market Impact [h2 + p] → Expert Perspective [blockquote] → My Take [h2 + p — personal analysis] → Outlook [h2 + p]",
    "intro_paragraph → The Context [h2 + p] → What Changed [h2 + p + ul] → Who Is Affected [h2 + p] → Analyst View [blockquote] → My Take [h2 + p — personal analysis] → Key Risks [h2 + p]",
    "intro_paragraph → Why It Matters Now [h2 + p] → Technical Breakdown [h2 + p + ul] → Industry Reaction [h2 + p] → Contrarian View [blockquote] → My Take [h2 + p — personal analysis] → What To Watch [h2 + p]",
    "intro_paragraph → The Bigger Picture [h2 + p] → Data In Focus [h2 + p] → Winners And Losers [h2 + p + ul] → Analyst Quote [blockquote] → My Take [h2 + p — personal analysis] → Bottom Line [h2 + p]",
]


def generate_article(title, topic, news_context, personal_analysis_html):
    structure = random.choice(ARTICLE_STRUCTURES)

    # نحدد موقع حقن الـ personal analysis داخل الـ HTML
    personal_analysis_placeholder = "<!-- PERSONAL_ANALYSIS_PLACEHOLDER -->"

    system_msg = """You are a Senior Technology Correspondent writing for Smart Flow Lab — the standard is Financial Times meets MIT Technology Review.

ABSOLUTE RULES:
1. HTML ONLY — use <h2>, <p>, <blockquote>, <ul>, <li>, <strong>, <em>. Zero Markdown.
2. GROUND IN REAL NEWS — reference provided headlines naturally (e.g. "According to [Source], ..."). Never invent sources.
3. NO INVENTED PEOPLE — never fabricate names. Use: "analysts note...", "industry observers...", "according to [real source]...".
4. NO INVENTED PRODUCTS — discuss real, confirmed technologies only.
5. NO FAKE STATISTICS — only cite numbers from the provided news context. Otherwise use ranges: "estimates range from X to Y".
6. BLOCKQUOTE format — one anonymous industry voice:
   <blockquote style="border-left: 3px solid #cc0000; padding: 12px 20px; margin: 20px 0; background: #fafafa; font-style: italic; color: #444;">
   "..." — <em>Senior analyst, [relevant sector]</em></blockquote>
7. PERSONAL ANALYSIS — insert this exact placeholder where "My Take" section belongs: <!-- PERSONAL_ANALYSIS_PLACEHOLDER -->
8. TONE — Analytical, precise, objective. No hype. Write like The Economist, not a press release.
9. LENGTH — 700–800 words of article content (excluding the placeholder).
10. H2 STYLE — every H2 must use: style="font-size: 22px; font-weight: bold; margin: 36px 0 14px; color: #111;"
11. P STYLE — every P must use: style="margin: 0 0 20px; font-size: 17px; line-height: 1.85; color: #1a1a1a;"
12. INTRO — first paragraph must open with a strong news hook — a surprising fact, a tension, or a key question."""

    user_msg = (
        f"Write a professional industry analysis article.\n\n"
        f"Title: {title}\n"
        f"Topic: {topic}\n"
        f"Date: {today_date}\n\n"
        f"Structure:\n{structure}\n\n"
        f"{news_context}\n\n"
        "Instructions:\n"
        "- Reference real news sources naturally inside the article\n"
        "- Insert <!-- PERSONAL_ANALYSIS_PLACEHOLDER --> exactly where 'My Take' section goes\n"
        "- Pure HTML, no Markdown\n"
        "- Be specific and analytical, not generic\n"
        "- Make the intro paragraph memorable — start with a fact, a contrast, or an open question"
    )

    raw = groq_call(system_msg, user_msg, max_tokens=2800, temp=0.45)
    if not raw:
        return None

    cleaned = markdown_to_html(raw)
    cleaned = post_process_html(cleaned)

    # حقن فقرة التحليل الشخصي في مكانها الصحيح
    if personal_analysis_placeholder in cleaned:
        cleaned = cleaned.replace(personal_analysis_placeholder, personal_analysis_html)
    else:
        # إذا نسي الموديل الـ placeholder، نضيف التحليل قبل آخر h2
        last_h2 = cleaned.rfind('<h2')
        if last_h2 != -1:
            cleaned = cleaned[:last_h2] + personal_analysis_html + cleaned[last_h2:]
        else:
            cleaned = cleaned + personal_analysis_html

    return cleaned

# ══════════════════════════════════════════════
#  PEXELS IMAGE
# ══════════════════════════════════════════════
def get_best_pexels_image(image_queries):
    try:
        query = random.choice(image_queries)
        url = (
            "https://api.pexels.com/v1/search"
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
#  HTML BUILDER — مع Google News signals
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

    # Reading time estimate (~200 words/min, article ~800 words)
    reading_time = "5 min read"

    return f"""
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>

<div style="font-family: 'Georgia', serif; line-height: 1.85; color: #1a1a1a; max-width: 820px; margin: auto; padding: 24px 20px;">

    <!-- Google News: clear byline + date in visible text is a ranking signal -->
    <header style="border-bottom: 3px solid #cc0000; padding-bottom: 18px; margin-bottom: 32px;">
        <p style="color: #cc0000; font-size: 12px; font-weight: bold; letter-spacing: 2px;
                  text-transform: uppercase; margin-bottom: 10px;">
            Smart Flow Lab &nbsp;|&nbsp; Technology Analysis
        </p>
        <h1 style="font-size: 34px; line-height: 1.25; font-weight: bold; margin-bottom: 14px; color: #111;">
            {title}
        </h1>
        <p style="color: #555; font-size: 13px; margin-bottom: 6px;">
            By <strong>Mohamed Ismaili</strong> &nbsp;&bull;&nbsp;
            <time datetime="{today_iso}">{today_date}</time> &nbsp;&bull;&nbsp;
            <em style="color: #888;">Senior Technology Analyst, Smart Flow Lab</em> &nbsp;&bull;&nbsp;
            <span style="color: #aaa;">{reading_time}</span>
        </p>
        <p style="color: #666; font-size: 15px; font-style: italic; margin-top: 12px;
                  border-left: 3px solid #ddd; padding-left: 12px;">
            {meta}
        </p>
    </header>

    <!-- Hero image with descriptive alt text (SEO signal) -->
    <figure style="margin: 0 0 32px 0;">
        <img src="{img}" alt="{title}"
             style="width: 100%; height: auto; border-radius: 6px; display: block;"
             loading="lazy">
        <figcaption style="font-size: 12px; color: #999; margin-top: 8px; text-align: center;
                           font-style: italic;">
            {title} — Smart Flow Lab / {today_date}
        </figcaption>
    </figure>

    <!-- Article body -->
    <article style="font-size: 17px; color: #1a1a1a;">
        {content}
    </article>

    {sources_html}

    <!-- Author bio — Google News requires clear authorship -->
    <div style="margin-top: 48px; padding: 24px; background: #f9f9f9;
                border-left: 4px solid #cc0000; border-radius: 0 4px 4px 0;">
        <strong style="font-size: 18px; color: #111;">About the Author</strong><br><br>
        <strong style="font-size: 16px; color: #222;">Mohamed Ismaili</strong><br>
        <span style="color: #555; font-size: 14px; line-height: 1.7;">
            Senior Technology Analyst at Smart Flow Lab. Mohamed covers artificial intelligence,
            semiconductor markets, cybersecurity infrastructure, and global digital policy.
            He has tracked the intersection of technology and geopolitics for over a decade,
            with a focus on how emerging markets — particularly in Africa and the Middle East —
            are being reshaped by digital transformation. Based in Morocco.
        </span>
    </div>

    <div style="margin-top: 24px; padding: 14px; background: #fff8f8;
                border: 1px solid #f0dede; border-radius: 4px; font-size: 12px; color: #888;">
        <strong>Editorial Note:</strong> This analysis is based on publicly available industry
        information and recent news sources. All opinions expressed are those of the author
        and do not constitute financial or investment advice.
    </div>

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
        raise

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════
def main():
    print("🚀 Smart Flow Lab Publisher v4.0 — starting...")

    # 1. تحميل التاريخ
    history = load_history()
    print(f"📋 Published so far: {len(history.get('topics', []))} topics, {len(history.get('titles', []))} titles")

    # 2. اختيار موضوع
    chosen        = get_next_topic(history)
    topic         = chosen["topic"]
    image_queries = chosen["image_queries"]
    newsapi_query = chosen["newsapi_query"]

    # 3. أخبار حقيقية
    print(f"📡 Fetching real news for: {newsapi_query}")
    articles     = fetch_real_news(newsapi_query, max_articles=5)
    news_context = format_news_for_prompt(articles)
    sources_html = build_sources_html(articles)

    # 4. Metadata مع عنوان جذاب
    title, keywords, meta = generate_meta(topic, history.get("titles", []))
    if not title:
        print("❌ Metadata generation failed. Stopping.")
        return

    # 5. تحقق من تكرار العنوان — حتى 5 محاولات
    attempts    = 1
    max_att     = 5
    curr_temp   = 0.45

    while is_title_duplicate(title, history) and attempts < max_att:
        curr_temp += 0.12
        print(f"⚠️ Duplicate title: '{title}' — retrying (attempt {attempts+1}, temp={curr_temp:.2f})")
        title, keywords, meta = generate_meta(topic, history.get("titles", []), temp=curr_temp)
        attempts += 1

    if not title or is_title_duplicate(title, history):
        print("❌ Could not generate unique title. Stopping.")
        return

    print(f"📰 Title: {title}")

    # 6. فقرة التحليل الشخصي
    print("✍️  Generating personal analysis paragraph...")
    personal_analysis_html = generate_personal_analysis(title, topic, news_context)

    # 7. المقال الكامل
    print("📝 Generating article...")
    content = generate_article(title, topic, news_context, personal_analysis_html)
    if not content:
        print("❌ Article generation failed. Stopping.")
        return

    # 8. الصورة
    img = get_best_pexels_image(image_queries)

    # 9. HTML الكامل
    full_html = build_full_html(title, content, img, meta, sources_html, keywords)

    # 10. النشر
    try:
        post_to_blogger_api(title, full_html, keywords)
        record_published(history, topic, title)
        print("🎉 Done! History updated.")
    except Exception as e:
        print(f"❌ Publish failed — history NOT updated: {e}")


if __name__ == "__main__":
    main()
