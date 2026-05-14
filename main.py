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
current_year = datetime.date.today().year

# ── Prompt ───────────────────────────────────────────────
# برومبت احترافي جداً مصمم خصيصاً للقبول في Google News و Google Ads
prompt = f"""
Current Date: {today_date}

You are an elite, Pulitzer-winning tech journalist writing an EXCLUSIVE, in-depth article for a world-class platform.
Your goal is to write a highly engaging, viral, and informative tech news article.

CRITICAL RULES FOR TOPIC:
- DO NOT write generic advice, tutorials, or "how-to" lists.
- FOCUS ONLY ON: New AI model releases, breakthrough scientific studies in tech, revolutionary educational tech tools for students, or major Silicon Valley updates happening RIGHT NOW in {current_year}.
- The article must feel like a breaking news report or an exclusive deep-dive analysis.

CRITICAL RULES FOR FORMATTING:
- Must be LONG and comprehensive (at least 800 - 1000 words).
- Write in flowing, engaging human paragraphs. 
- Organize the article logically with catchy, journalistic subheadings (H2) for EVERY new section.
- Use a professional, analytical, yet accessible tone.

YOU MUST FORMAT YOUR EXACT RESPONSE USING THESE TAGS:
[TITLE] Write a catchy, click-worthy but professional journalistic title (Max 70 chars).
[KEYWORDS] 3-4 specific English words describing a visual scene for the cover photo (e.g., "ai server room", "student laptop laboratory").
[META] Write a compelling SEO meta description (150 chars).
[CONTENT]
Write the full article HTML here. Use ONLY <p>, <h2>, <h3>, <strong>, <em>, and <blockquote>. Do NOT use markdown. Ensure every section has an <h2> heading.
"""

def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.75,
            max_tokens=4000,
        )
        raw = completion.choices[0].message.content

        # استخراج دقيق جداً باستعمال Regex متطور لتفادي أي تداخل
        title_match = re.search(r"\[TITLE\](.*?)\[KEYWORDS\]", raw, re.DOTALL | re.IGNORECASE)
        kw_match = re.search(r"\[KEYWORDS\](.*?)\[META\]", raw, re.DOTALL | re.IGNORECASE)
        meta_match = re.search(r"\[META\](.*?)\[CONTENT\]", raw, re.DOTALL | re.IGNORECASE)
        content_match = re.search(r"\[CONTENT\](.*)", raw, re.DOTALL | re.IGNORECASE)

        title = title_match.group(1).strip() if title_match else "Exclusive Tech Update: Breaking Innovations in AI"
        keywords = kw_match.group(1).strip() if kw_match else "technology future artificial intelligence"
        meta_desc = meta_match.group(1).strip() if meta_match else f"Discover the latest breakthroughs in technology and artificial intelligence for {current_year}."
        
        if content_match:
            content = content_match.group(1).strip()
            # تنظيف أي Markdown زائد بخطوة واحدة صحيحة
            content = re.sub(r'```html|
```', '', content).strip()
        else:
            return None, None, None, None

        return title, keywords, meta_desc, content

    except Exception as e:
        print(f"❌ Generation error: {e}")
        return None, None, None, None

# ── Pexels Logic ──────────────────────────────────────────
def get_best_pexels_image(keywords):
    if not PEXELS_KEY:
        return f"https://picsum.photos/seed/{urllib.parse.quote(keywords)}/1200/630"
    
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(f"https://api.pexels.com/v1/search?query={keywords}&per_page=3&orientation=landscape", headers=headers, timeout=10)
        data = res.json()
        if data.get("photos"):
            # نأخذ أول صورة عالية الجودة
            return data["photos"][0]["src"]["large2x"]
    except Exception as e:
        print(f"⚠️ Pexels error: {e}")
    
    # Fallback
    return f"https://picsum.photos/seed/ai-tech/1200/630"

# ── Build & Send ──────────────────────────────────────────
title, keywords, meta_desc, article_body = generate_content()

if title and article_body:
    image_url = get_best_pexels_image(keywords)
    
    # قالب HTML احترافي جداً مصمم لـ Google News و Ads
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="description" content="{meta_desc}">
<style>
  body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #202124; line-height: 1.8; }}
  .article-container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
  .category-tag {{ background-color: #1a73e8; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
  h1 {{ font-size: 36px; font-weight: 800; line-height: 1.3; margin-top: 15px; margin-bottom: 15px; color: #111; }}
  .author-date {{ font-size: 14px; color: #5f6368; border-bottom: 1px solid #dadce0; padding-bottom: 15px; margin-bottom: 25px; }}
  .author-date strong {{ color: #202124; }}
  .featured-image {{ width: 100%; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
  .content p {{ font-size: 18px; margin-bottom: 24px; color: #3c4043; text-align: justify; }}
  .content p:first-of-type::first-letter {{ font-size: 50px; font-weight: bold; color: #1a73e8; float: left; margin-right: 8px; line-height: 1; }}
  .content h2 {{ font-size: 26px; font-weight: 700; color: #202124; margin-top: 40px; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e8eaed; }}
  .content blockquote {{ font-style: italic; font-size: 20px; border-left: 4px solid #1a73e8; margin: 30px 0; padding-left: 20px; color: #555; background: #f8f9fa; padding: 15px 20px; border-radius: 0 8px 8px 0; }}
  .footer-note {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #dadce0; font-size: 13px; color: #80868b; text-align: center; }}
</style>
</head>
<body>
<div class="article-container">
  <span class="category-tag">Exclusive Report</span>
  <h1>{title}</h1>
  <div class="author-date">By <strong>Smart Flow Lab</strong> | Published on {today_date}</div>
  
  <img src="{image_url}" alt="{title}" class="featured-image">
  
  <div class="content">
    {article_body}
  </div>
  
  <div class="footer-note">
    © {current_year} Smart Flow Lab - Tech & AI Journalism. All rights reserved.
  </div>
</div>
</body>
</html>
"""

    msg = MIMEText(full_html, 'html', 'utf-8')
    
    # حيدنا #News باش العنوان يكون نقي ومناسب لـ Google News
    msg['Subject'] = title
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Success! Published: {title}")
    except Exception as e:
        print(f"❌ Mail Error: {e}")
else:
    print("❌ Content generation failed completely. The AI did not return the expected format.")
