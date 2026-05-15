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
NEWSAPI_KEY   = os.environ.get("NEWSAPI_KEY")          # 🆕 Add this in your env
CLIENT_ID     = os.environ.get("BLOGGER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN")

client       = Groq(api_key=GROQ_KEY)
today_iso    = datetime.datetime.now().isoformat()
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = datetime.date.today().year

# ══════════════════════════════════════════════
#  TOPICS — كل موضوع عنده keywords للأخبار الحقيقية
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
    }
]

# ══════════════════════════════════════════════
#  🆕 NEWSAPI — جلب أخبار حقيقية
# ══════════════════════════════════════════════
def fetch_real_news(query, max_articles=5):
    """
    جلب أخبار حقيقية من NewsAPI لاستخدامها كأساس للمقال.
    يرجع قائمة من: title, source, url, description
    """
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
    """
    تحويل الأخبار المجلوبة إلى نص منظم للـ prompt.
    """
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
    """
    بناء قسم Sources في نهاية المقال — ضروري لـ Google News E-E-A-T.
    """
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
#  🆕 GROQ — نموذج أقوى + retry
# ══════════════════════════════════════════════
def groq_call(system_msg, user_msg, max_tokens=2500):
    # 🆕 نموذج 70b بدل 8b — جودة أعلى بكثير
    MODEL = "llama-3.3-70b-versatile"

    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg}
                ],
                model=MODEL,
                temperature=0.45,   # أقل عشوائية = أكثر دقة
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
def generate_meta(topic):
    system_msg = "You are a professional News SEO strategist. Generate metadata without fluff."
    user_msg = (
        f"Generate metadata for: {topic}.\n"
        "Output ONLY in this format:\n"
        "[TITLE] (max 65 chars, news-style headline)\n"
        "[KEYWORDS] (3 comma-separated terms)\n"
        "[META] (one compelling sentence under 155 chars)"
    )
    raw = groq_call(system_msg, user_msg, max_tokens=300)
    if not raw:
        return None, None, None

    t = re.search(r"\[TITLE\]\s*(.*)",    raw, re.I)
    k = re.search(r"\[KEYWORDS\]\s*(.*)", raw, re.I)
    m = re.search(r"\[META\]\s*(.*)",     raw, re.I)

    title    = t.group(1).strip() if t else f"Update: {topic}"
    keywords = k.group(1).strip() if k else "Tech, News, Innovation"
    meta     = m.group(1).strip() if m else f"Latest analysis on {topic}."
    return title, keywords, meta

# ══════════════════════════════════════════════
#  🆕 ARTICLE GENERATOR — بأخبار حقيقية + هياكل متنوعة
# ══════════════════════════════════════════════

# هياكل مختلفة كل مرة — يتجنب الـ spam filter
ARTICLE_STRUCTURES = [
    "intro <p> → Section 1 <h2>+<p> → Section 2 <h2>+<p> → Key Takeaway <blockquote> → Outlook <h2>+<p> → Conclusion <p>",
    "intro <p> → Background <h2>+<p> → Current Developments <h2>+<p><ul> → Expert View <blockquote> → What's Next <h2>+<p>",
    "intro <p> → Market Context <h2>+<p> → Technical Analysis <h2>+<p> → Industry Impact <h2>+<p> → Analyst Quote <blockquote> → Summary <p>",
    "intro <p> → The Challenge <h2>+<p> → The Solution Landscape <h2>+<p><ul> → Numbers in Context <h2>+<p> → Forward Outlook <blockquote>+<p>",
]


def generate_article(title, topic, news_context):
    structure = random.choice(ARTICLE_STRUCTURES)

    system_msg = """You are a Senior Tech Analyst at Smart Flow Lab writing a professional industry analysis.

ABSOLUTE RULES:
1. HTML ONLY — use <h2>, <p>, <blockquote>, <ul>, <li>, <strong>, <em>. Zero Markdown.
2. GROUND IN REAL NEWS — the user provides recent news headlines; reference them naturally 
   (e.g. "According to [Source], ..."). NEVER invent sources not listed.
3. NO INVENTED PEOPLE — no fake names. Use: "analysts note...", "industry observers suggest...",
   "according to [real source from context]...".
4. NO INVENTED PRODUCTS — discuss real confirmed technologies only.
5. NO FAKE STATISTICS — if citing a number, it must come from the provided news context.
   Otherwise use: "estimates vary", "industry reports suggest ranges of X to Y".
6. BLOCKQUOTE format — anonymous industry voice:
   <blockquote style="border-left: 3px solid #cc0000; padding: 12px 20px; margin: 20px 0; 
   background: #fafafa; font-style: italic; color: #444;">
   "..." — <em>Senior analyst, [relevant sector]</em></blockquote>
7. TONE — Analytical, precise, objective. No hype. Write like The Economist, not a press release.
8. LENGTH — 750–850 words of actual content."""

    user_msg = (
        f"Write an industry analysis article.\n\n"
        f"Title: {title}\n"
        f"Topic: {topic}\n"
        f"Date: {today_date}\n\n"
        f"Structure to follow:\n{structure}\n\n"
        f"{news_context}\n\n"
        "Instructions:\n"
        "- Reference the real news sources naturally inside the article\n"
        "- Pure HTML only, no Markdown\n"
        "- Be specific and analytical, not generic"
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
#  🆕 HTML BUILDER — قسم Sources + Schema محسّن
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

    <!-- 🆕 SOURCES SECTION -->
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

        # 🆕 labels من الـ keywords الحقيقية
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

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════
def main():
    print("🚀 Smart Flow Lab Publisher v2 — starting...")

    # 1. اختيار الموضوع
    chosen        = random.choice(TOPIC_ANGLES)
    topic         = chosen["topic"]
    image_queries = chosen["image_queries"]
    newsapi_query = chosen["newsapi_query"]

    # 2. جلب أخبار حقيقية
    print(f"📡 Fetching real news for: {newsapi_query}")
    articles      = fetch_real_news(newsapi_query, max_articles=5)
    news_context  = format_news_for_prompt(articles)
    sources_html  = build_sources_html(articles)

    # 3. توليد الـ metadata
    title, keywords, meta = generate_meta(topic)
    if not title:
        print("❌ Metadata generation failed. Stopping.")
        return
    print(f"📰 Title: {title}")

    # 4. توليد المقال بأخبار حقيقية
    content = generate_article(title, topic, news_context)
    if not content:
        print("❌ Article generation failed. Stopping.")
        return

    # 5. الصورة
    img = get_best_pexels_image(image_queries)

    # 6. بناء HTML الكامل
    full_html = build_full_html(title, content, img, meta, sources_html, keywords)

    # 7. النشر
    post_to_blogger_api(title, full_html, keywords)
    print("🎉 Done!")


if __name__ == "__main__":
    main()
