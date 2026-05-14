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
today_date = datetime.date.today().strftime("%B %d, %2026")
current_year = 2026

# ── Prompt ───────────────────────────────────────────────
prompt = f"""
Current Date: {today_date}

You are an elite tech journalist for Wired/The Verge. 
TASK: Write a 1000-word EXCLUSIVE investigative report on a major tech breakthrough in {current_year}.

TOPIC IDEAS: 
- New AI-Human neural interfaces.
- The 2026 Quantum Computing leap.
- How AI is revolutionizing CPGE and high-level engineering education.
- Silicon Valley's next big ethical crisis.

FORMAT:
[TITLE] Catchy journalistic title.
[KEYWORDS] 3-4 visual words for a high-quality photo.
[META] 150-char SEO description.
[CONTENT] Full HTML article. Use <h2>, <p>, <blockquote>, <strong>. No markdown.
"""

def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=4000,
        )
        raw = completion.choices[0].message.content

        # Regex Extraction
        title = re.search(r"\[TITLE\](.*?)\[", raw, re.S | re.I)
        kw = re.search(r"\[KEYWORDS\](.*?)\[", raw, re.S | re.I)
        meta = re.search(r"\[META\](.*?)\[", raw, re.S | re.I)
        content = re.search(r"\[CONTENT\](.*)", raw, re.S | re.I)

        final_title = title.group(1).strip() if title else "Tech Breakthrough 2026"
        final_kw = kw.group(1).strip() if kw else "innovation technology"
        final_meta = meta.group(1).strip() if meta) else "Latest exclusive tech news."
        
        if content:
            article = content.group(1).strip()
            # الإصلاح هنا: سطر واحد لتنظيف الكود
            article = article.replace("```html", "").replace("
```", "").strip()
        else:
            return None, None, None, None

        return final_title, final_kw, final_meta, article
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None, None

def get_pexels_image(keywords):
    if not PEXELS_KEY: return "https://picsum.photos/1200/630"
    try:
        url = f"https://api.pexels.com/v1/search?query={keywords}&per_page=1&orientation=landscape"
        r = requests.get(url, headers={{"Authorization": PEXELS_KEY}}, timeout=10)
        return r.json()['photos'][0]['src']['large2x']
    except:
        return f"https://picsum.photos/seed/{{urllib.parse.quote(keywords)}}/1200/630"

# ── Processing ───────────────────────────────────────────
t, k, m, body = generate_content()

if t and body:
    img = get_pexels_image(k)
    
    html = f"""
    <html>
    <head><meta name="description" content="{{m}}"></head>
    <body style="font-family: 'Segoe UI', sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: auto; padding: 20px;">
        <span style="color: #1a73e8; font-weight: bold; text-transform: uppercase;">Exclusive Report</span>
        <h1 style="font-size: 38px; margin-top: 10px;">{{t}}</h1>
        <p style="color: #777; border-bottom: 1px solid #eee; padding-bottom: 15px;">Smart Flow Lab | {{today_date}}</p>
        <img src="{{img}}" style="width: 100%; border-radius: 12px; margin: 20px 0;">
        <div style="font-size: 19px;">{{body}}</div>
        <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #aaa;">© 2026 Smart Flow Lab</div>
    </body>
    </html>
    """

    msg = MIMEText(html, 'html', 'utf-8')
    msg['Subject'] = t
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(MY_GMAIL, GMAIL_PASS)
        s.send_message(msg)
    print(f"✅ Published: {{t}}")
