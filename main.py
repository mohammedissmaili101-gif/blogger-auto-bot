import os
import smtplib
import re
import datetime
import urllib.parse
import requests
import random
import traceback
from email.message import EmailMessage
from groq import Groq

# ── Secrets ──────────────────────────────────────────────
GROQ_KEY      = os.environ.get("GROQ_API_KEY")
GMAIL_PASS    = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL  = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL      = os.environ.get("MY_GMAIL")
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY")
SENDER_GMAIL  = os.environ.get("SENDER_GMAIL")
SENDER_PASS   = os.environ.get("SENDER_GMAIL_PASS")

client       = Groq(api_key=GROQ_KEY)
today_date   = datetime.date.today().strftime("%B %d, %Y")
current_year = str(datetime.date.today().year)

# ── Topic Rotation System ─────────────────────────────────
TOPIC_ANGLES = [
    "the most disruptive NEW AI model released this week in " + current_year + " — cover its benchmarks, real-world impact, and what it means for the industry",
    "a BREAKTHROUGH scientific study published in " + current_year + " that is reshaping how we understand human cognition, learning, or productivity using technology",
    "a revolutionary AI-powered tool JUST LAUNCHED for students or researchers in " + current_year + " that is changing how people study, write, or learn",
    "a major SILICON VALLEY corporate shakeup, acquisition, or product pivot happening RIGHT NOW in " + current_year + " that is sending shockwaves through the tech world",
    "a cutting-edge AI application in healthcare, climate tech, or education that just received massive funding or produced landmark results in " + current_year,
    "the fierce battle between two or more AI giants (e.g., OpenAI vs Google vs Meta vs Anthropic) over a specific capability or market in " + current_year + " — with exclusive analysis",
    "how a newly released AI coding or developer tool in " + current_year + " is transforming software engineering and what it means for the future of work",
    "a viral, trend-setting AI use case that regular people are adopting RIGHT NOW in " + current_year + " — explain the why, the how, and the societal impact",
]

chosen_topic = random.choice(TOPIC_ANGLES)

# ── Prompt ───────────────────────────────────────────────
prompt = (
    "Current Date: " + today_date + "\n\n"
    "You are a Pulitzer Prize-winning investigative tech journalist for a world-class publication like The Atlantic or MIT Technology Review.\n\n"
    "YOUR ASSIGNED STORY TODAY:\n"
    "Write an EXCLUSIVE, deeply reported, analytical article about: " + chosen_topic + "\n\n"
    "ABSOLUTE RULES — VIOLATIONS WILL RESULT IN REJECTION:\n"
    "1. NO generic advice, no how-to lists, no \"Top 10\" formats.\n"
    "2. The article must read like BREAKING NEWS or an EXCLUSIVE DEEP-DIVE ANALYSIS.\n"
    "3. You MUST invent realistic, specific details: quote real or plausible expert names with titles, cite plausible study figures, mention real company names, real model names, and real recent events. Make it feel 100% real and sourced.\n"
    "4. Vary your sentence length — mix short punchy sentences with long analytical ones.\n"
    "5. The opening paragraph must be a powerful HOOK that grabs the reader immediately.\n"
    "6. Minimum 900 words. Maximum 1200 words.\n"
    "7. The title must be UNDER 65 characters — no hashtags (#), no asterisks (*), no special symbols.\n"
    "   The title MUST be UNIQUE and SPECIFIC to this exact story — never use generic phrases like\n"
    "   \"The AI Breakthrough\" or \"Reshaping Tech\". Make it punchy, specific, and different every time.\n\n"
    "STRUCTURE REQUIRED (use these exact HTML tags):\n"
    "- One powerful <p> opening hook (no heading before it)\n"
    "- Then alternate: <h2> section heading -> 2-3 <p> paragraphs -> repeat\n"
    "- Use <blockquote> for at least ONE expert quote\n"
    "- Use <strong> for key terms, company names, model names\n"
    "- Use <em> for emphasis on critical insights\n"
    "- End with a forward-looking <h2> conclusion section\n\n"
    "CRITICAL FORMATTING RULE — MANDATORY:\n"
    "You MUST start your response with exactly these 4 tags on separate lines.\n"
    "Do NOT add any text, greeting, or preamble before [TITLE].\n"
    "Do NOT skip any tag.\n"
    "The format must be EXACTLY as shown below — no deviations:\n\n"
    "[TITLE] your title here\n"
    "[KEYWORDS] your keywords here\n"
    "[META] your meta description here\n"
    "[CONTENT]\n"
    "your full HTML article here using ONLY <p>, <h2>, <h3>, <strong>, <em>, <blockquote>. No markdown. No code fences.\n"
)

# ── CSS ───────────────────────────────────────────────────
CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --ink:       #0d0d0d;
    --ink-light: #3a3a3a;
    --ink-muted: #6b6b6b;
    --rule:      #e2e2e2;
    --accent:    #c0392b;
    --accent-bg: #fff8f7;
    --bg:        #fafaf8;
    --white:     #ffffff;
  }
  body {
    font-family: 'Source Serif 4', Georgia, serif;
    background: var(--bg);
    color: var(--ink);
    font-size: 19px;
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
  }
  .top-bar {
    background: var(--ink);
    color: var(--white);
    text-align: center;
    padding: 10px 20px;
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }
  .masthead {
    border-bottom: 3px double var(--ink);
    padding: 18px 20px 14px;
    text-align: center;
  }
  .masthead-name {
    font-family: 'Playfair Display', serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: var(--ink);
  }
  .masthead-rule {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px auto;
    max-width: 340px;
  }
  .masthead-rule span {
    flex: 1;
    height: 1px;
    background: var(--ink);
  }
  .masthead-rule em {
    font-family: 'DM Sans', sans-serif;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--ink-muted);
    font-style: normal;
  }
  .article-wrap {
    max-width: 740px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }
  .category-tag {
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
  }
  h1.headline {
    font-family: 'Playfair Display', serif;
    font-size: clamp(30px, 5vw, 48px);
    font-weight: 800;
    line-height: 1.15;
    color: var(--ink);
    margin-bottom: 18px;
    letter-spacing: -0.01em;
  }
  .byline {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    letter-spacing: 0.04em;
    margin-bottom: 30px;
  }
  .byline strong {
    color: var(--ink);
    font-weight: 500;
  }
  .featured-image-wrap {
    margin: 0 -24px 36px;
    position: relative;
  }
  .featured-image-wrap img {
    width: 100%;
    max-height: 480px;
    object-fit: cover;
    display: block;
  }
  .image-caption {
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: var(--ink-muted);
    padding: 8px 24px 0;
    letter-spacing: 0.02em;
  }
  .content p {
    margin-bottom: 26px;
    color: var(--ink-light);
    hyphens: auto;
  }
  .content > p:first-child::first-letter {
    font-family: 'Playfair Display', serif;
    font-size: 72px;
    font-weight: 800;
    float: left;
    line-height: 0.78;
    margin-right: 6px;
    margin-top: 10px;
    color: var(--accent);
  }
  .content h2 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(20px, 3vw, 26px);
    font-weight: 700;
    color: var(--ink);
    margin: 48px 0 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--ink);
    letter-spacing: -0.01em;
  }
  .content h3 {
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    font-weight: 500;
    color: var(--ink-muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin: 36px 0 12px;
  }
  .content blockquote {
    border-left: 4px solid var(--accent);
    background: var(--accent-bg);
    margin: 36px 0;
    padding: 20px 24px;
    border-radius: 0 4px 4px 0;
  }
  .content blockquote p {
    font-style: italic;
    font-size: 20px;
    line-height: 1.65;
    color: var(--ink);
    margin-bottom: 8px !important;
  }
  .content blockquote cite {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    font-style: normal;
    letter-spacing: 0.06em;
  }
  .content strong { color: var(--ink); font-weight: 600; }
  .content em { font-style: italic; }
  .pull-rule {
    text-align: center;
    color: var(--rule);
    font-size: 24px;
    letter-spacing: 0.3em;
    margin: 40px 0;
  }
  .article-footer {
    margin-top: 60px;
    padding-top: 24px;
    border-top: 3px double var(--ink);
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: var(--ink-muted);
    text-align: center;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
"""

# ── Robust Parser ────────────────────────────────────────
def parse_response(raw):
    if not isinstance(raw, str):
        raw = str(raw)

    normalized = re.sub(
        r'\[\s*(TITLE|KEYWORDS|META|CONTENT)\s*\]',
        lambda m: "[" + m.group(1).upper() + "]",
        raw, flags=re.IGNORECASE
    )
    normalized = re.sub(r'\[CONTENT[:\s]*\]', '[CONTENT]', normalized, flags=re.IGNORECASE)

    title_match   = re.search(r"\[TITLE\](.*?)(?=\[KEYWORDS\]|\[META\]|\[CONTENT\]|$)", normalized, re.DOTALL)
    kw_match      = re.search(r"\[KEYWORDS\](.*?)(?=\[META\]|\[CONTENT\]|\[TITLE\]|$)", normalized, re.DOTALL)
    meta_match    = re.search(r"\[META\](.*?)(?=\[CONTENT\]|\[TITLE\]|\[KEYWORDS\]|$)", normalized, re.DOTALL)
    content_match = re.search(r"\[CONTENT\](.*)", normalized, re.DOTALL)

    if not content_match:
        html_match = re.search(r'(<(?:p|h2|h3|blockquote)[^>]*>.*)', normalized, re.DOTALL | re.IGNORECASE)
        if html_match:
            print("WARNING: [CONTENT] tag missing — extracted HTML body directly.")
            content_raw = html_match.group(1)
        else:
            lines = normalized.split('\n')
            content_raw = None
            for i, line in enumerate(lines):
                if re.search(r'\[META\]', line, re.IGNORECASE) and i + 1 < len(lines):
                    content_raw = '\n'.join(lines[i + 2:]).strip()
                    print("WARNING: Fallback: extracted content after [META] line.")
                    break
            if not content_raw:
                print("ERROR: Could not extract article content from AI response.")
                print(raw[:500])
                return None, None, None, None
    else:
        content_raw = content_match.group(1)

    if title_match:
        title = str(title_match.group(1)).strip()
    else:
        print("WARNING: [TITLE] missing — requesting unique title from Groq...")
        try:
            fallback = client.chat.completions.create(
                messages=[{"role": "user", "content": "Write ONE punchy SEO-optimized news headline under 65 chars about: " + chosen_topic + ". Return ONLY the headline, nothing else. No quotes, no symbols."}],
                model="llama-3.3-70b-versatile",
                max_tokens=50,
            )
            title = str(fallback.choices[0].message.content).strip()
        except Exception as e:
            print("WARNING: Fallback title failed: " + str(e))
            title = "AI Exclusive: " + today_date

    keywords = str(kw_match.group(1)).strip()   if kw_match   else "technology, AI, innovation"
    meta_raw = str(meta_match.group(1)).strip() if meta_match else "Discover the latest breakthroughs in AI and technology for " + current_year + "."

    title = re.sub(r'[#*`]', '', title).strip()
    title = re.sub(r'^[\s\-:]+|[\s\-:]+$', '', title).strip()

    meta_desc = meta_raw[:160].strip()
    content   = str(content_raw).strip()
    content   = re.sub(r'```[\w]*|```', '', content)
    content   = re.sub(r'##\s+(.*?)(\n|$)', r'<h2>\1</h2>', content)
    content   = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content   = re.sub(r'\*(.*?)\*',     r'<em>\1</em>',         content)
    content   = content.strip()

    return title, keywords, meta_desc, content


# ── Content Generation (with retry) ──────────────────────
def generate_content(max_retries=3):
    for attempt in range(1, max_retries + 1):
        print("AI attempt " + str(attempt) + "/" + str(max_retries) + "...")
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.80,
                max_tokens=4096,
            )
            raw = completion.choices[0].message.content
            if not isinstance(raw, str):
                raw = str(raw)
            result = parse_response(raw)
            if result[0] is not None:
                return result
            print("WARNING: Parse failed on attempt " + str(attempt) + ". Retrying...")
        except Exception as e:
            print("ERROR: API error on attempt " + str(attempt) + ": " + str(e))

    print("ERROR: All retries exhausted. Generation failed.")
    return None, None, None, None


# ── Pexels Image ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    keywords = str(keywords).strip()
    fallback_keywords = [keywords, "technology innovation bright", "artificial intelligence future bright"]

    if not PEXELS_KEY:
        return "https://picsum.photos/seed/" + urllib.parse.quote(keywords, safe="") + "/1200/628"

    headers = {"Authorization": str(PEXELS_KEY)}

    for kw in fallback_keywords:
        try:
            kw  = str(kw).strip()
            url = (
                "https://api.pexels.com/v1/search"
                "?query=" + urllib.parse.quote(kw, safe="") +
                "&per_page=10"
                "&orientation=landscape"
                "&size=large"
            )
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data   = res.json()
            photos = data.get("photos", [])

            if photos:
                best = None
                for photo in photos:
                    avg_color = photo.get("avg_color", "#000000")
                    try:
                        r = int(avg_color[1:3], 16)
                        g = int(avg_color[3:5], 16)
                        b = int(avg_color[5:7], 16)
                        brightness = (r * 299 + g * 587 + b * 114) / 1000
                    except Exception:
                        brightness = 0
                    if brightness > 80:
                        best = photo
                        break
                if best:
                    return str(best["src"]["large2x"])
                elif photos:
                    return str(photos[0]["src"]["large2x"])

        except Exception as e:
            print("WARNING: Pexels error for '" + str(kw) + "': " + str(e))
            continue

    return "https://picsum.photos/seed/" + urllib.parse.quote(keywords, safe="") + "/1200/628"


# ── HTML Builder ──────────────────────────────────────────
def build_html(title, meta_desc, image_url, article_body):
    title        = str(title).strip()
    meta_desc    = str(meta_desc).strip()
    image_url    = str(image_url).strip()
    article_body = str(article_body).strip()
    t_date       = str(today_date)
    t_year       = str(current_year)

    title_safe = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    meta_safe  = meta_desc.replace('"', '&quot;')

    parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<meta name="description" content="' + meta_safe + '">',
        '<meta property="og:title" content="' + title_safe + '">',
        '<meta property="og:description" content="' + meta_safe + '">',
        '<meta property="og:image" content="' + image_url + '">',
        '<meta property="og:type" content="article">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">',
        '<style>',
        CSS,
        '</style>',
        '</head>',
        '<body>',
        '<div class="top-bar">Smart Flow Lab &nbsp;|&nbsp; Tech &amp; AI Intelligence &nbsp;|&nbsp; ' + t_date + '</div>',
        '<div class="masthead">',
        '  <div class="masthead-name">Smart Flow Lab</div>',
        '  <div class="masthead-rule">',
        '    <span></span>',
        '    <em>Exclusive Report</em>',
        '    <span></span>',
        '  </div>',
        '</div>',
        '<article class="article-wrap">',
        '  <span class="category-tag">&#9632; Breaking Analysis</span>',
        '  <h1 class="headline">' + title + '</h1>',
        '  <div class="byline">',
        '    By <strong>Smart Flow Lab Editorial Team</strong> &nbsp;|&nbsp; ' + t_date + ' &nbsp;|&nbsp; 6 min read',
        '  </div>',
        '  <div class="featured-image-wrap">',
        '    <img src="' + image_url + '" alt="' + title_safe + '" loading="eager">',
        '    <p class="image-caption">Image: Smart Flow Lab / ' + t_date + '</p>',
        '  </div>',
        '  <div class="content">',
        '    ' + article_body,
        '  </div>',
        '  <div class="pull-rule">&#8901; &nbsp; &#8901; &nbsp; &#8901;</div>',
        '  <footer class="article-footer">',
        '    &copy; ' + t_year + ' Smart Flow Lab &mdash; All rights reserved &nbsp;|&nbsp;',
        '    Reproduction without permission is prohibited',
        '  </footer>',
        '</article>',
        '</body>',
        '</html>',
    ]

    # Safety check: force every item to str before joining
    safe_parts = [str(p) for p in parts]
    return '\n'.join(safe_parts)


# ── Send Email ────────────────────────────────────────────
def send_email(title, html_body):
    title     = str(title).strip()
    html_body = str(html_body).strip()

    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"]    = str(SENDER_GMAIL)
    msg["To"]      = str(BLOGGER_MAIL)
    msg.set_content("Please enable HTML to view this email.")
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(str(SENDER_GMAIL), str(SENDER_PASS))
            server.send_message(msg)
        print("SUCCESS: Published: " + title)
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP Auth failed. Check Gmail App Password.")
    except smtplib.SMTPException as e:
        print("ERROR: SMTP Error: " + str(e))
    except Exception as e:
        traceback.print_exc()
        print("ERROR: General Error: " + str(e))


# ── Main ──────────────────────────────────────────────────
def main():
    print("Today's angle: " + chosen_topic[:80] + "...")
    print("Generating article...")

    title, keywords, meta_desc, article_body = generate_content()

    if not title or not article_body:
        print("ERROR: Generation failed. AI response format was unexpected.")
        return

    title        = str(title).strip()
    keywords     = str(keywords).strip()
    meta_desc    = str(meta_desc).strip()
    article_body = str(article_body).strip()

    print("Title   : " + title)
    print("Keywords: " + keywords)
    print("Meta    : " + meta_desc)

    print("Fetching image...")
    image_url = str(get_best_pexels_image(keywords)).strip()
    print("Image   : " + image_url)

    print("Building HTML...")
    full_html = build_html(title, meta_desc, image_url, article_body)

    print("Sending to Blogger...")
    send_email(title, full_html)

if __name__ == "__main__":
    main()
