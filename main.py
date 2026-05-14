import os
import smtplib
import re
import random
from email.mime.text import MIMEText
from groq import Groq

# 1. جلب السوارت من البيئة (GitHub Secrets)
GROQ_KEY = os.environ.get("GROQ_API_KEY")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL = os.environ.get("MY_GMAIL")

client = Groq(api_key=GROQ_KEY)

# 2. البرومبت "الصحفي" لضمان جودة Google News
prompt = """
Act as an expert tech journalist for a world-class magazine like 'The Verge' or 'Wired'. 
Task: Write a high-impact, professional article in English.
Focus: A specific recent AI tool, a productivity scientific study, or a breakthrough in tech.

Format your response EXACTLY like this:
TITLE: [Catchy, journalistic title here]
KEYWORDS: [3-4 comma-separated English keywords for a professional photo related to the topic]
CONTENT:
[Write the article here using ONLY professional HTML. 
Use <h2 style="color: #1a73e8; border-bottom: 2px solid #eee; padding-bottom: 10px;"> for subheadings.
Use <p style="font-size: 16px; line-height: 1.8; color: #333;"> for paragraphs.
Ensure the tone is human, analytical, and exclusive. No AI-cliches.]
"""

def generate_content():
    try:
        # هنا تم تحديث الموديل لنسخة Llama 3.3 لضمان استمرار العمل
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.6, 
        )
        raw_text = completion.choices[0].message.content
        
        # تقسيم الاستجابة بدقة
        title_match = re.search(r"TITLE:(.*)", raw_text)
        keywords_match = re.search(r"KEYWORDS:(.*)", raw_text)
        
        if title_match and keywords_match and "CONTENT:" in raw_text:
            title = title_match.group(1).strip()
            keywords = keywords_match.group(1).strip().replace(" ", "")
            content = raw_text.split("CONTENT:")[1].strip()
            return title, keywords, content
        else:
            print("Error: AI response format is incorrect.")
            return None, None, None
            
    except Exception as e:
        print(f"Error generating content: {e}")
        return None, None, None

# 3. جلب صورة مطابقة للموضوع
def get_relevant_image(keywords):
    return f"https://loremflickr.com/1200/630/{keywords}/all"

title, keywords, article_body = generate_content()

if title:
    image_url = get_relevant_image(keywords)
    
    # 4. التنسيق النهائي للمقال (Magazine Style)
    full_html = f"""
    <div style="max-width: 800px; margin: auto; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <h1 style="font-size: 36px; color: #111; line-height: 1.2; margin-bottom: 20px;">{title}</h1>
        <img src="{image_url}" alt="{title}" style="width: 100%; height: auto; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <div style="text-align: justify;">
            {article_body}
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 40px 0;">
        <p style="color: #888; font-style: italic;">&copy; 2026 Smart Flow Lab AI - Tech Reportage</p>
    </div>
    """

    # 5. إرسال الإيميل مع إضافة Label التصنيف (News)
    msg = MIMEText(full_html, 'html')
    # إضافة #News للعنوان باش بلوجر يصنفو تلقائياً
    msg['Subject'] = f"{title} #News" 
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ Success! Published in News: {title}")
    except Exception as e:
        print(f"❌ Mail Error: {e}")
