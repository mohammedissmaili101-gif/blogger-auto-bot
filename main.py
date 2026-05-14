import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
from email.mime.text import MIMEText
from groq import Groq

# ── Secrets ──────────────────────────────────────────────
GROQ_KEY     = os.environ.get("GROQ_API_KEY")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL     = os.environ.get("MY_GMAIL")
PEXELS_KEY   = os.environ.get("PEXELS_API_KEY")

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = datetime.date.today().year

# ── Topic Rotation System ─────────────────────────────────
# كل مرة يختار موضوع مختلف عشوائياً لضمان التنوع
TOPIC_ANGLES = [
    f"the most disruptive NEW AI model released this week in {current_year} — cover its benchmarks, real-world impact, and what it means for the industry",
    f"a BREAKTHROUGH scientific study published in {current_year} that is reshaping how we understand human cognition, learning, or productivity using technology",
    f"a revolutionary AI-powered tool JUST LAUNCHED for students or researchers in {current_year} that is changing how people study, write, or learn",
    f"a major SILICON VALLEY corporate shakeup, acquisition, or product pivot happening RIGHT NOW in {current_year} that is sending shockwaves through the tech world",
    f"a cutting-edge AI application in healthcare, climate tech, or education that just received massive funding or produced landmark results in {current_year}",
    f"the fierce battle between two or more AI giants (e.g., OpenAI vs Google vs Meta vs Anthropic) over a specific capability or market in {current_year} — with exclusive analysis",
    f"how a newly released AI coding or developer tool in {current_year} is transforming software engineering and what it means for the future of work",
    f"a viral, trend-setting AI use case that regular people are adopting RIGHT NOW in {current_year} — explain the why, the how, and the societal impact",
]

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}

You are a Pulitzer Prize-winning investigative tech journalist for a world-class publication like The Atlantic or MIT Technology Review.

YOUR ASSIGNED STORY TODAY:
Write an EXCLUSIVE, deeply reported, analytical article about: {chosen_topic}

ABSOLUTE RULES — VIOLATIONS WILL RESULT IN REJECTION:
1. NO generic advice, no how-to lists, no "Top 10" formats.
2. The article must read like BREAKING NEWS or an EXCLUSIVE DEEP-DIVE ANALYSIS.
3. You MUST invent realistic, specific details: quote real or plausible expert names with titles, cite plausible study figures, mention real company names, real model names, and real recent events. Make it feel 100% real and sourced.
4. Vary your sentence length — mix short punchy sentences with long analytical ones.
5. The opening paragraph must be a powerful HOOK that grabs the reader immediately.
6. Minimum 900 words. Maximum 1200 words.
7. The title must be UNDER 65 characters — no hashtags (#), no asterisks (*), no special symbols.

STRUCTURE REQUIRED (use these exact HTML tags):
- One powerful <p> opening hook (no heading before it)
- Then alternate: <h2> section heading → 2-3 <p> paragraphs → repeat
- Use <blockquote> for at least ONE expert quote
- Use <strong> for key terms, company names, model names
- Use <em> for emphasis on critical insights
- End with a forward-looking <h2> conclusion section

YOU MUST FORMAT YOUR EXACT RESPONSE USING THESE TAGS (no extra text outside them):
[TITLE] One clean journalistic title, max 65 chars, NO special symbols.
[KEYWORDS] 4 vivid English words for a photojournalism-quality cover image (e.g., "scientist laboratory neural network", "developer laptop glowing code"). Must be BRIGHT, COLORFUL, and RELEVANT — avoid dark/abstract scenes.
[META] A compelling 140-char SEO description.
[CONTENT]
Full article HTML here using ONLY <p>, <h2>, <h3>, <strong>, <em>, <blockquote>. No markdown. No code fences.
"""

# ── Content Generation ────────────────────────────────────
def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.80,
            max_tokens=4096,
        )
        raw = completion.choices[0].message.content

        title_match   = re.search(r"\[TITLE\](.*?)\[KEYWORDS\]", raw, re.DOTALL | re.IGNORECASE)
        kw_match      = re.search(r"\[KEYWORDS\](.*?)\[META\]",   raw, re.DOTALL | re.IGNORECASE)
        meta_match    = re.search(r"\[META\](.*?)\[CONTENT\]",    raw, re.DOTALL | re.IGNORECASE)
        content_match = re.search(r"\[CONTENT\](.*)",             raw, re.DOTALL | re.IGNORECASE)

        title    = title_match.group(1).strip() if title_match else "Exclusive: The AI Breakthrough Reshaping Tech"
        keywords = kw_match.group(1).strip()    if kw_match   else "bright technology innovation laboratory"
        meta_raw = meta_match.group(1).strip()  if meta_match else f"Discover the latest breakthroughs in AI and technology for {current_year}."

        # Trim to 160 chars & clean
        meta_desc = meta_raw[:160].strip()

        # Remove any ## or ** or ``` leftovers from title
        title = re.sub(r'[#*`]', '', title).strip()

        if content_match:
            content = content_match.group(1).strip()
            # Clean markdown fences and stray backticks
            content = re.sub(r'```[\w]*|```', '', content).strip()
            # Remove any remaining ## headings (convert to h2)
            content = re.sub(r'##\s+(.*?)(\n|$)', r'<h2>\1</h2>', content)
            # Remove stray asterisks used as bold markdown
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        else:
            print("❌ [CONTENT] tag not found in AI response.")
            return None, None, None, None

        return title, keywords, meta_desc, content

    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None, None, None

# ── Pexels Image (bright, relevant) ──────────────────────
def get_best_pexels_image(keywords):
    """
    Fetches a bright, high-quality, landscape image from Pexels.
    Tries multiple keyword fallbacks to avoid dark/irrelevant images.
    """
    fallback_keywords = [keywords, "technology innovation bright", "artificial intelligence future bright"]

    if not PEXELS_KEY:
        return f"https://picsum.photos/seed/{urllib.parse.quote(keywords)}/1200/628"

    headers = {"Authorization": PEXELS_KEY}

    for kw in fallback_keywords:
        try:
            url = (
                f"https://api.pexels.com/v1/search"
                f"?query={urllib.parse.quote(kw)}"
                f"&per_page=10"
                f"&orientation=landscape"
                f"&size=large"
            )
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            photos = data.get("photos", [])

            if photos:
                # Pick photo with highest avg_color brightness (skip dark ones)
                best = None
                for photo in photos:
                    avg_color = photo.get("avg_color", "#000000")
                    # Convert hex to brightness
                    try:
                        r = int(avg_color[1:3], 16)
                        g = int(avg_color[3:5], 16)
                        b = int(avg_color[5:7], 16)
                        brightness = (r * 299 + g * 587 + b * 114) / 1000
                    except Exception:
                        brightness = 0

                    if brightness > 80:  # Only bright images
                        best = photo
                        break

                if best:
                    return best["src"]["large2x"]
                elif photos:
                    # Fallback: take first available even if dark
                    return photos[0]["src"]["large2x"]

        except Exception as e:
            print(f"⚠️ Pexels error for '{kw}': {e}")
            continue

    return f"https://picsum.photos/seed/{urllib.parse.quote(keywords)}/1200/628"

# ── Magazine-Quality HTML Builder ────────────────────────
def build_html(title, meta_desc, image_url, article_body):
    title_safe = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    meta_safe  = meta_desc.replace('"', '&quot;')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{meta_safe}">
<meta property="og:title" content="{title_safe}">
<meta property="og:description" content="{meta_safe}">
<meta property="og:image" content="{image_url}">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --ink:       #0d0d0d;
    --ink-light: #3a3a3a;
    --ink-muted: #6b6b6b;
    --rule:      #e2e2e2;
    --accent:    #c0392b;
    --accent-bg: #fff8f7;
    --bg:        #fafaf8;
    --white:     #ffffff;
  }}

  body {{
    font-family: 'Source Serif 4', Georgia, serif;
    background: var(--bg);
    color: var(--ink);
    font-size: 19px;
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── TOP BAR ── */
  .top-bar {{
    background: var(--ink);
    color: var(--white);
    text-align: center;
    padding: 10px 20px;
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }}

  /* ── MASTHEAD ── */
  .masthead {{
    border-bottom: 3px double var(--ink);
    padding: 18px 20px 14px;
    text-align: center;
  }}
  .masthead-name {{
    font-family: 'Playfair Display', serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: var(--ink);
  }}
  .masthead-rule {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px auto;
    max-width: 340px;
  }}
  .masthead-rule span {{
    flex: 1;
    height: 1px;
    background: var(--ink);
  }}
  .masthead-rule em {{
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-muted);
    font-style: normal;
  }}

  /* ── ARTICLE WRAPPER ── */
  .article-wrap {{
    max-width: 740px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }}

  /* ── CATEGORY TAG ── */
  .category-tag {{
    display: inline-block;
    background: var(--accent);
    color: var(--white);
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    padding: 5px 12px;
    margin-bottom: 20px;
  }}

  /* ── HEADLINE ── */
  h1.headline {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(30px, 5vw, 48px);
    font-weight: 800;
    line-height: 1.15;
    color: var(--ink);
    margin-bottom: 18px;
    letter-spacing: -0.01em;
  }}

  /* ── DECK / SUBHEAD ── */
  .deck {{
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    color: var(--ink-muted);
    line-height: 1.6;
    border-top: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
    padding: 12px 0;
    margin-bottom: 22px;
  }}

  /* ── BYLINE ── */
  .byline {{
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    letter-spacing: 0.04em;
    margin-bottom: 30px;
  }}
  .byline strong {{
    color: var(--ink);
    font-weight: 500;
  }}

  /* ── FEATURED IMAGE ── */
  .featured-image-wrap {{
    margin: 0 -24px 36px;
    position: relative;
  }}
  .featured-image-wrap img {{
    width: 100%;
    max-height: 480px;
    object-fit: cover;
    display: block;
  }}
  .image-caption {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: var(--ink-muted);
    padding: 8px 24px 0;
    letter-spacing: 0.02em;
  }}

  /* ── ARTICLE CONTENT ── */
  .content p {{
    margin-bottom: 26px;
    color: var(--ink-light);
    hyphens: auto;
  }}

  /* Drop cap on first paragraph */
  .content > p:first-child::first-letter {{
    font-family: 'Playfair Display', serif;
    font-size: 72px;
    font-weight: 800;
    float: left;
    line-height: 0.78;
    margin-right: 6px;
    margin-top: 10px;
    color: var(--accent);
  }}

  .content h2 {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(20px, 3vw, 26px);
    font-weight: 700;
    color: var(--ink);
    margin: 48px 0 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--ink);
    letter-spacing: -0.01em;
  }}

  .content h3 {{
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    font-weight: 500;
    color: var(--ink-muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin: 36px 0 12px;
  }}

  .content blockquote {{
    border-left: 4px solid var(--accent);
    background: var(--accent-bg);
    margin: 36px 0;
    padding: 20px 24px;
    border-radius: 0 4px 4px 0;
  }}
  .content blockquote p {{
    font-style: italic;
    font-size: 20px;
    line-height: 1.65;
    color: var(--ink);
    margin-bottom: 8px !important;
  }}
  .content blockquote cite {{
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    font-style: normal;
    letter-spacing: 0.06em;
  }}

  .content strong {{ color: var(--ink); font-weight: 600; }}
  .content em {{ font-style: italic; }}

  /* ── PULL QUOTE RULE ── */
  .pull-rule {{
    text-align: center;
    color: var(--rule);
    font-size: 24px;
    letter-spacing: 0.3em;
    margin: 40px 0;
  }}

  /* ── FOOTER ── */
  .article-footer {{
    margin-top: 60px;
    padding-top: 24px;
    border-top: 3px double var(--ink);
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: var(--ink-muted);
    text-align: center;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
</style>
</head>
<body>

<div class="top-bar">Smart Flow Lab &nbsp;|&nbsp; Tech &amp; AI Intelligence &nbsp;|&nbsp; {today_date}</div>

<div class="masthead">
  <div class="masthead-name">Smart Flow Lab</div>
  <div class="masthead-rule">
    <span></span>
    <em>Exclusive Report</em>
    <span></span>
  </div>
</div>

<article class="article-wrap">

  <span class="category-tag">&#9632; Breaking Analysis</span>

  <h1 class="headline">{title}</h1>

  <div class="byline">
    By <strong>Smart Flow Lab Editorial Team</strong> &nbsp;|&nbsp; {today_date} &nbsp;|&nbsp; 6 min read
  </div>

  <div class="featured-image-wrap">
    <img src="{image_url}" alt="{title_safe}" loading="eager">
    <p class="image-caption">Image: Smart Flow Lab / {today_date}</p>
  </div>

  <div class="content">
    {article_body}
  </div>

  <div class="pull-rule">&#8901; &nbsp; &#8901; &nbsp; &#8901;</div>

  <footer class="article-footer">
    &copy; {current_year} Smart Flow Lab &mdash; All rights reserved &nbsp;|&nbsp;
    Reproduction without permission is prohibited
  </footer>

</article>
</body>
</html>
"""

# ── Send Email ────────────────────────────────────────────
def send_email(title, html_body):
    msg            = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = title          # Clean title, no ## symbols
    msg['From']    = MY_GMAIL
    msg['To']      = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Published: {title}")
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Auth failed. Check Gmail App Password.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
    except Exception as e:
        print(f"❌ General Error: {e}")

# ── Main ──────────────────────────────────────────────────
def main():
    print(f"📌 Today's angle: {chosen_topic[:80]}...")
    print("🔄 Generating article...")

    title, keywords, meta_desc, article_body = generate_content()

    if not title or not article_body:
        print("❌ Generation failed. AI response format was unexpected.")
        return

    print(f"📰 Title   : {title}")
    print(f"🔍 Keywords: {keywords}")
    print(f"📝 Meta    : {meta_desc}")

    print("🖼️  Fetching image...")
    image_url = get_best_pexels_image(keywords)
    print(f"🌅 Image   : {image_url}")

    print("🏗️  Building HTML...")
    full_html = build_html(title, meta_desc, image_url, article_body)

    print("📧 Sending to Blogger...")
    send_email(title, full_html)

if __name__ == "__main__":
    main()
