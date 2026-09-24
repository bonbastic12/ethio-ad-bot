import os
import sqlite3
import threading
from flask import Flask
import telebot

# Render ፖርት እንዲያገኝ ትንሽዬ Web Server
app = Flask(__name__)

@app.route('/')
def home():
    return "Ethio Ad Bot is Running Live!"

# የቦት ቶከን
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# የዳታቤዝ ዝግጅት
def init_db():
    conn = sqlite3.connect('ads.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_name TEXT,
            channel_link TEXT,
            base_price INTEGER,
            final_price INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# /start ትዕዛዝ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "እንኳን ደህና መጡ! 📢\n\n"
        "• ቻናልዎን ለማስመዝገብ፦ /register የሚለውን ይጫኑ።\n"
        "• ማስታወቂያዎችን ለመመልከት ከታች ያለውን የዌብሳይት ቁልፍ ይጠቀሙ።"
    )
    bot.reply_to(message, text)

# ቻናል ምዝገባ
@bot.message_handler(commands=['register'])
def start_register(message):
    msg = bot.reply_to(message, "እባክዎ የቻናልዎን ስም ያስገቡ (ለምሳሌ፦ MR ODDS):")
    bot.register_next_step_handler(msg, process_channel_name)

def process_channel_name(message):
    channel_name = message.text
    msg = bot.reply_to(message, "የቻናሉን ሊንክ ያስገቡ (ለምሳሌ፦ https://t.me/MRBENJA12):")
    bot.register_next_step_handler(msg, process_channel_link, channel_name)

def process_channel_link(message, channel_name):
    channel_link = message.text
    msg = bot.reply_to(message, "የሚፈልጉትን የ24 ሰዓት የማስታወቂያ ዋጋ በብር ብቻ ያስገቡ (ለምሳሌ፦ 1300):")
    bot.register_next_step_handler(msg, process_price, channel_name, channel_link)

def process_price(message, channel_name, channel_link):
    try:
        base_price = int(message.text.strip())
        commission = 200
        final_price = base_price + commission  # 200 ብር ኮሚሽን በራሱ ይደምራል

        conn = sqlite3.connect('ads.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO channels (user_id, channel_name, channel_link, base_price, final_price)
            VALUES (?, ?, ?, ?, ?)
        ''', (message.chat.id, channel_name, channel_link, base_price, final_price))
        conn.commit()
        conn.close()

        success_text = (
            f"✅ ቻናልዎ በተሳካ ሁኔታ ተመዝግቧል!\n\n"
            f"📢 ቻናል፦ {channel_name}\n"
            f"💰 የእርስዎ ዋጋ፦ {base_price} ብር\n"
            f"🏷 በገበያ ላይ የሚቀርብበት ዋጋ፦ {final_price} ብር (+200 ብር የአገልግሎት ክፍያ)\n\n"
            f"ማስታወቂያ ሲታዘዝ በቦቱ በኩል እናሳውቅዎታለን!"
        )
        bot.reply_to(message, success_text)
    except ValueError:
        bot.reply_to(message, "❌ ዋጋውን በቁጥር ብቻ ያስገቡ (ለምሳሌ፦ 1500)። እንደገና /register ብለው ይሞክሩ።")

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    # ቦቱን በጀርባ (background) ያስነሳል
    threading.Thread(target=run_bot, daemon=True).start()
    # Render የሚፈልገውን ፖርት ከፍቶ ይጠብቃል
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
