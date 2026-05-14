import os
import smtplib
import re
import datetime
import urllib.parse
import requests
from email.mime.text import MIMEText
from groq import Groq

# ── Secrets ──────────────────────────────────────────────
GROQ_KEY     = os.environ.get("GROQ_API_KEY")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

client     = Groq(api_key=GROQ_KEY)
today_date = datetime.date.today().strftime("%B %d, %Y")
today_year = datetime.date.today().year

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}

You are a Pulitzer-level investigative tech journalist writing for Wired Magazine.
Your articles are read by millions. You write with passion, depth, and humanity.

TASK: Write one EXCLUSIVE, LONG investigative tech article ({today_year} only).

TOPIC — choose the most viral one today:
1. A Generative AI breakthrough or ethical controversy in {today_year}
2. Human-AI collaboration transforming education, medicine, or creativity
3. Robotics entering everyday life in surprising ways
4. A Silicon Valley power shift, acquisition, or startup disruption
5. Quantum computing or brain-computer interface milestone

═══ WRITING STYLE (CRITICAL) ═══
- Voice: Passionate, curious, slightly opinionated human journalist
- Tone: Smart but accessible — NYT meets Wired
- Use: "I spoke with...", "What surprised me was...", "The question nobody is asking..."
- Include 2–3 quotes from realistic named fictional experts (name + title + institution)
- NO bullet points in body text — flowing narrative paragraphs only
- Show tension, stakes, and human impact in every section
- Minimum 1000 words

═══ STRUCTURE (follow exactly) ═══
1. Powerful 2-sentence hook (what changed today and why it matters)
2. Context paragraph (background in 3–4 sentences)
3. H2: The Core Breakthrough / The Controversy
4. H2: Who's Behind It — and Why Now
5. H2: What Experts Are Saying
6. H2: The Human Side of the Story
7. H2: What This Means for You
8. Strong editorial conclusion (your opinion as journalist)

═══ SEO & GOOGLE NEWS ═══
- Title: max 70 chars, journalistic, no clickbait
- First 40 words: answer who/what/when/where/why
- H2 every 250 words minimum
- Meta description: exactly 150–155 chars

═══ IMAGE KEYWORDS (CRITICAL) ═══
SLUG_KEYWORDS must be:
- 3 to 5 specific English words describing a VISUAL SCENE
- Match the article's main subject exactly
- Be concrete and searchable on a photo library
- Examples of GOOD keywords:
  * "humanoid robot factory worker"
  * "scientist quantum computer laboratory"
  * "student laptop AI hologram classroom"
  * "silicon valley office startup team"
- Examples of BAD keywords (too vague):
  * "technology innovation future"
  * "digital transformation"
  * "artificial intelligence"

═══ OUTPUT FORMAT (exact, no deviation) ═══
TITLE: [title]
SLUG_KEYWORDS: [3-5 specific visual English words]
FALLBACK_KEYWORDS: [3-5 alternative visual English words if first search fails]
META_DESC: [150-155 char description]
CONTENT:
[HTML using ONLY: <p> <h2> <h3> <blockquote> <strong> <em> — nothing else]
"""

# ── Generate Content ──────────────────────────────────────
def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.78,
            max_tokens=3500,
        )
        raw = completion.choices[0].message.content

        title        = re.search(r"TITLE:\s*(.+)",           raw).group(1).strip()
        slug_kw      = re.search(r"SLUG_KEYWORDS:\s*(.+)",   raw).group(1).strip()
        fallback_kw  = re.search(r"FALLBACK_KEYWORDS:\s*(.+)", raw)
        fallback_kw  = fallback_kw.group(1).strip() if fallback_kw else "technology computer screen"
        meta_desc    = re.search(r"META_DESC:\s*(.+)",       raw).group(1).strip()
        content      = raw.split("CONTENT:")[1].strip()

        # نظف markdown
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*',     r'<em>\1</em>',         content)
        content = re.sub(r'```.*?```',     '',  content, flags=re.DOTALL)
        content = re.sub(r'#+\s',          '',  content)

        return title, slug_kw, fallback_kw, meta_desc, content

    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None, None, None, None

# ── Smart Pexels Image Selector ───────────────────────────
def search_pexels(query: str, per_page: int = 10):
    """ابحث في Pexels وارجع قائمة الصور"""
    try:
        res = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            timeout=10
        )
        data = res.json()
        return data.get("photos", [])
    except Exception as e:
        print(f"⚠️ Pexels search error: {e}")
        return []

def score_photo(photo: dict, keywords: str) -> int:
    """
    احسب score للصورة بناءً على:
    - عدد الكلمات المفتاحية الموجودة في alt/photographer
    - حجم الصورة (الأكبر = أفضل جودة)
    - وجود landscape orientation
    """
    score = 0
    kw_list = [k.strip().lower() for k in keywords.replace(",", " ").split()]

    # تحقق من alt text
    alt = photo.get("alt", "").lower()
    for kw in kw_list:
        if kw in alt:
            score += 10   # كل كلمة مفتاحية موجودة في alt = +10

    # فضّل الصور الأعرض (landscape حقيقية)
    width  = photo.get("width", 0)
    height = photo.get("height", 0)
    if width > height:
        score += 5
    if width >= 1920:
        score += 3

    # فضّل الصور ذات liked_count (إذا وجد)
    score += photo.get("liked", 0) // 1000

    return score

def get_best_pexels_image(primary_kw: str, fallback_kw: str) -> str:
    """
    1. ابحث بالكلمات الأساسية
    2. score كل صورة واختر الأعلى
    3. إذا ما لقيناش → جرب fallback keywords
    4. إذا ما لقيناش → Picsum seed
    """
    print(f"🔍 Searching Pexels: '{primary_kw}'")
    photos = search_pexels(primary_kw, per_page=10)

    # إذا ما رجعت نتائج → جرب fallback
    if not photos:
        print(f"⚠️ No results — trying fallback: '{fallback_kw}'")
        photos = search_pexels(fallback_kw, per_page=10)

    # إذا لا زال فاضي → جرب كلمة واحدة عامة من primary
    if not photos:
        single_kw = primary_kw.split()[0]
        print(f"⚠️ Still no results — trying single keyword: '{single_kw}'")
        photos = search_pexels(single_kw, per_page=5)

    if photos:
        # رتّب الصور حسب الـ score
        scored = sorted(photos, key=lambda p: score_photo(p, primary_kw), reverse=True)
        best   = scored[0]
        url    = best["src"]["large2x"]  # 1880px — جودة عالية
        alt    = best.get("alt", "")
        print(f"✅ Best photo selected: '{alt}' (score: {score_photo(best, primary_kw)})")
        return url

    # Fallback نهائي: Picsum بـ seed ثابت
    print("⚠️ Using Picsum fallback")
    seed = urllib.parse.quote_plus(primary_kw)
    return f"https://picsum.photos/seed/{seed}/1200/630"

# ── HTML Template ─────────────────────────────────────────
def build_html(title, meta_desc, image_url, article_body, today_date):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{meta_desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:image" content="{image_url}">
<meta property="og:type" content="article">
<meta name="robots" content="index, follow">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #ffffff; -webkit-font-smoothing: antialiased; }}
  .article-wrap {{
    max-width: 780px;
    margin: 0 auto;
    padding: 48px 24px 80px;
  }}
  .top-bar {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e5e5e5;
  }}
  .section-tag {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #fff;
    background: #c0392b;
    padding: 4px 10px;
    border-radius: 2px;
  }}
  .exclusive-tag {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #c0392b;
    border: 1.5px solid #c0392b;
    padding: 3px 8px;
    border-radius: 2px;
  }}
  h1 {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 44px;
    font-weight: 900;
    line-height: 1.08;
    color: #0a0a0a;
    margin-bottom: 20px;
    letter-spacing: -0.5px;
  }}
  .byline {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: #888;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 0;
    border-top: 2px solid #0a0a0a;
    border-bottom: 1px solid #ddd;
    margin-bottom: 32px;
    flex-wrap: wrap;
  }}
  .byline strong {{ color: #111; font-weight: 700; }}
  .byline .dot {{ color: #ccc; }}
  .hero-img {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 3px;
  }}
  .img-caption {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
    color: #aaa;
    margin-top: 8px;
    margin-bottom: 36px;
    font-style: italic;
    padding-left: 4px;
    border-left: 2px solid #eee;
  }}
  .article-body p {{
    font-family: 'Georgia', serif;
    font-size: 19px;
    line-height: 1.9;
    margin-bottom: 26px;
    color: #1a1a1a;
  }}
  .article-body p:first-child::first-letter {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 72px;
    font-weight: 900;
    float: left;
    line-height: 0.75;
    margin: 8px 10px 0 0;
    color: #0a0a0a;
  }}
  .article-body h2 {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 27px;
    font-weight: 800;
    margin: 48px 0 18px;
    color: #0a0a0a;
    padding-bottom: 10px;
    border-bottom: 2px solid #f0f0f0;
    border-left: 5px solid #c0392b;
    padding-left: 16px;
    line-height: 1.3;
  }}
  .article-body h3 {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 21px;
    font-weight: 700;
    margin: 32px 0 14px;
    color: #222;
  }}
  .article-body blockquote {{
    border: none;
    border-left: 5px solid #0a0a0a;
    margin: 40px 0;
    padding: 20px 28px;
    background: #fafafa;
    border-radius: 0 6px 6px 0;
  }}
  .article-body blockquote p {{
    font-size: 22px !important;
    font-style: italic;
    color: #222;
    line-height: 1.6 !important;
    margin-bottom: 10px !important;
  }}
  .article-body blockquote p:first-child::first-letter {{
    font-size: 22px !important;
    float: none !important;
    margin: 0 !important;
  }}
  .article-body blockquote cite {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: #888;
    font-style: normal;
    display: block;
    margin-top: 6px;
  }}
  .article-body strong {{ font-weight: 700; color: #000; }}
  .article-body em {{ font-style: italic; color: #444; }}
  .article-footer {{
    margin-top: 64px;
    padding: 24px 0 0;
    border-top: 3px solid #0a0a0a;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .brand-block .brand-name {{
    font-size: 18px;
    font-weight: 900;
    color: #0a0a0a;
    letter-spacing: -0.3px;
  }}
  .brand-block .brand-name span {{ color: #c0392b; }}
  .brand-block .brand-sub {{
    font-size: 11px;
    color: #bbb;
    margin-top: 4px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .footer-right {{
    text-align: right;
    font-size: 12px;
    color: #aaa;
    line-height: 1.7;
  }}
</style>
</head>
<body>
<div class="article-wrap">

  <div class="top-bar">
    <span class="section-tag">Technology</span>
    <span class="section-tag" style="background:#1a1a2e;">AI</span>
    <span class="exclusive-tag">Exclusive</span>
  </div>

  <h1>{title}</h1>

  <div class="byline">
    <strong>Smart Flow Lab</strong>
    <span class="dot">·</span>
    <span>{today_date}</span>
    <span class="dot">·</span>
    <span>5 min read</span>
    <span class="dot">·</span>
    <span>Exclusive Report</span>
  </div>

  <div class="hero-wrap">
    <img src="{image_url}" alt="{title}" class="hero-img" loading="eager">
    <div class="img-caption">Photo via Pexels &nbsp;·&nbsp; Smart Flow Lab / {today_date}</div>
  </div>

  <div class="article-body">
    {article_body}
  </div>

  <div class="article-footer">
    <div class="brand-block">
      <div class="brand-name">Smart Flow <span>Lab</span></div>
      <div class="brand-sub">Tech Journalism · Est. 2024</div>
    </div>
    <div class="footer-right">
      AI-Assisted · Human-Edited<br>
      {today_date}<br>
      <em>smartflowlab.com</em>
    </div>
  </div>

</div>
</body>
</html>"""

# ── Main ──────────────────────────────────────────────────
title, slug_kw, fallback_kw, meta_desc, article_body = generate_content()

if title:
    image_url = get_best_pexels_image(slug_kw, fallback_kw)
    full_html = build_html(title, meta_desc, image_url, article_body, today_date)

    msg = MIMEText(full_html, 'html', 'utf-8')
    msg['Subject'] = f"{title} #News"
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published: {title}")
        print(f"🖼️  Image: {image_url}")
        print(f"🏷️  Label: News")
    except Exception as e:
        print(f"❌ Mail Error: {e}")
else:
    print("❌ Content generation failed.")
