import os
import smtplib
import re
import datetime
from email.mime.text import MIMEText
from groq import Groq

# 1. جلب السوارت من البيئة (GitHub Secrets)
GROQ_KEY = os.environ.get("GROQ_API_KEY")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD")
BLOGGER_MAIL = os.environ.get("BLOGGER_EMAIL")
MY_GMAIL = os.environ.get("MY_GMAIL")

client = Groq(api_key=GROQ_KEY)

# جلب تاريخ اليوم لضمان مواضيع حصرية (Trend)
today_date = datetime.date.today().strftime("%B %d, %2026")

# 2. البرومبت المطور (Journalist Pro v2)
prompt = f"""
Current Date: {today_date}
Act as a Senior Tech Editor at Wired or TechCrunch. 
Task: Write a viral, trending tech news article about a major 2026 breakthrough.
Topics: Generative AI, Robotics, Quantum Computing, or Silicon Valley shifts.

CRITICAL RULES:
- Do NOT write about old news like Llama 2 or GPT-4. Focus on 2026 innovations.
- TITLE: Must be catchy and journalistic.
- KEYWORDS: Provide 3 keywords related to high-tech/professional imagery.
- CONTENT: Use professional HTML. Start with a strong lead paragraph.

Format:
TITLE: [Title]
KEYWORDS: [3 keywords]
CONTENT: [HTML Content]
"""

def generate_content():
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", 
            temperature=0.7, # زيادة الحرارة شوية للإبداع
        )
        raw_text = completion.choices[0].message.content
        
        # استخراج البيانات بذكاء أكبر
        title = re.search(r"TITLE:(.*)", raw_text).group(1).strip()
        # إضافة كلمة technology للكلمات المفتاحية لضمان صور تقنية
        keywords = re.search(r"KEYWORDS:(.*)", raw_text).group(1).strip().replace(" ", "") + ",technology"
        content = raw_text.split("CONTENT:")[1].strip()
        
        return title, keywords, content
    except Exception as e:
        print(f"Error generating content: {e}")
        return None, None, None

# 3. جلب صورة احترافية
def get_relevant_image(keywords):
    # إضافة "tech" لضمان جودة الصور
    return f"https://loremflickr.com/1200/630/{keywords}/all"

title, keywords, article_body = generate_content()

if title:
    image_url = get_relevant_image(keywords)
    
    # 4. التنسيق (حيدنا #News من العنوان الداخلي)
    full_html = f"""
    <div style="max-width: 800px; margin: auto; font-family: 'Helvetica Neue', Arial, sans-serif; color: #222;">
        <h1 style="font-size: 38px; font-weight: 800; line-height: 1.1; margin-bottom: 25px; color: #111;">{title}</h1>
        <p style="color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px;">Tech Report | {today_date}</p>
        <img src="{image_url}" alt="{title}" style="width: 100%; border-radius: 12px; margin-bottom: 30px;">
        <div style="font-size: 18px; line-height: 1.8; text-align: justify;">
            {article_body}
        </div>
        <div style="margin-top: 50px; padding: 20px; background: #f9f9f9; border-radius: 8px; text-align: center;">
            <p style="margin: 0; color: #555; font-weight: bold;">Smart Flow Lab AI</p>
            <p style="margin: 5px 0 0; color: #999; font-size: 12px;">Automated Tech Journalism v2.0</p>
        </div>
    </div>
    """

    # 5. الإرسال (الوسم #News كيبقى غي في السابجيكت باش يخدم الفلتر في بلوجر)
    msg = MIMEText(full_html, 'html')
    msg['Subject'] = f"{title} #News" 
    msg['From'] = MY_GMAIL
    msg['To'] = BLOGGER_MAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_GMAIL, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ مغيز! Published: {title}")
    except Exception as e:
        print(f"❌ Mail Error: {e}")
