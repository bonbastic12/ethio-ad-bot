import os
import random
import smtplib
from email.mime.text import MIMEText
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, LabeledPrice
from google import genai

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
ADMIN_ID = 6179388927

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

CBE_ACCOUNT = "1000785625556"
TELEBIRR_NUM = "0927943402"
ABYSSINIA_ACCOUNT = "218988407"
ACCOUNT_NAME = "Wo..."

TON_WALLET = "UQCxUAhKH0Zlj_LT2-fDtktqVZ7sFsLNS47-pfqOK_MiOjnm"
TRC20_WALLET = "TSTAsyXoWR8CqWLP2yGaFgJ385vJs2WeR8"
ERC20_WALLET = "0x8929FF9b5cE44E4c433318D6321AFF2c077Ed9DF"

RENDER_URL = "https://ethio-ad-bot-wz6h.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

LANG_STRINGS = {
    "en": {
        "welcome": "Welcome! 📢\n\n• Register channel: /register\n• Buy ad: /buy_ad\n• Change language: /lang\n• Cancel operation: /cancel\n• Chat with AI: /ask or type your question.",
        "lang_set": "Language switched to English.",
        "enter_ch_name": "Enter channel name:",
        "enter_ch_link": "Enter channel link:",
        "enter_price": "Enter starting price (ETB):",
        "registered": "✅ Channel registered successfully!",
        "pay_title": "💳 *Payment Instructions*\n\n📢 *Channel:* {channel}\n⏳ *Duration:* {duration}\n💰 *Total:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 Payment approved! Please send the ad content.",
        "posted": "🎉 Ad published to {channel}!"
    },
    "am": {
        "welcome": "እንኳን ደህና መጡ! 📢\n\n• ቻናል ለመመዝገብ፦ /register\n• ማስታወቂያ ለመግዛት፦ /buy_ad\n• ቋንቋ ለመቀየር፦ /lang\n• አሰራር ለመሰረዝ፦ /cancel\n• AI ለማናገር፦ /ask ወይም በቀጥታ ጽፈው ይላኩ።",
        "lang_set": "ቋንቋው ወደ አማርኛ ተቀይሯል።",
        "enter_ch_name": "እባክዎ የቻናልዎን ስም ያስገቡ (ለምሳሌ፦ MR ODDS):",
        "enter_ch_link": "የቻናሉን ሊንክ ያስገቡ (ለምሳሌ፦ https://t.me/wodtech1):",
        "enter_price": "የሚፈልጉትን የመነሻ ዋጋ በብር ያስገቡ (ለምሳሌ፦ 1000):",
        "registered": "✅ ቻናልዎ በተሳካ ሁኔታ ተመዝግቧል!",
        "pay_title": "💳 *የክፍያ መመሪያ*\n\n📢 *ቻናል፦* {channel}\n⏳ *ቆይታ፦* {duration}\n💰 *ዋጋ፦* {price} ETB (ወይም ~{usd}$ USD)",
        "ad_prompt": "🎉 ክፍያዎ ጸድቋል! እባክዎ በቻናሉ እንዲለጠፍ የሚፈልጉትን ማስታወቂያ እዚህ ይላኩ።",
        "posted": "🎉 ማስታወቂያዎ በቀጥታ በ {channel} ቻናል ላይ በተሳካ ሁኔታ ተለጥፏል!"
    }
}

DURATION_OPTIONS = {
    "24h": {"label": "24h (1 Day)", "extra": 0},
    "48h": {"label": "48h (2 Days)", "extra": 300},
    "1w":  {"label": "1 Week (7 Days)", "extra": 600},
    "2w":  {"label": "2 Weeks (14 Days)", "extra": 900},
    "1m":  {"label": "1 Month (30 Days)", "extra": 1200},
    "2m":  {"label": "2 Months (60 Days)", "extra": 1500}
}

user_lang = {}
user_orders = {}
approved_users = {}
active_otps = {}

def get_text(chat_id, key):
    lang = user_lang.get(chat_id, "en")
    return LANG_STRINGS.get(lang, LANG_STRINGS["en"]).get(key, LANG_STRINGS["en"].get(key, ""))

def get_db_connection():
    conn = sqlite3.connect('ads.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/channels', methods=['GET'])
def get_channels():
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()
    return jsonify([dict(row) for row in channels])

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    contact = data.get('contact', '').strip()
    country_code = data.get('country_code', '+251')

    if not contact:
        return jsonify({'status': 'error', 'message': 'Contact is required'}), 400

    otp_code = str(random.randint(10000, 99999))
    active_otps[contact] = otp_code

    if "@" in contact and SMTP_EMAIL and SMTP_PASSWORD:
        try:
            msg = MIMEText(f"Your EthioAd.io Verification Code is: {otp_code}")
            msg['Subject'] = "EthioAd.io Verification Code"
            msg['From'] = SMTP_EMAIL
            msg['To'] = contact
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, [contact], msg.as_string())
            server.quit()
        except:
            pass

    try:
        bot.send_message(ADMIN_ID, f"🔐 *Web Verification Code*\n\nTarget: `{contact}`\nCountry: `{country_code}`\n5-Digit Code: `{otp_code}`", parse_mode="Markdown")
    except:
        pass

    return jsonify({
        'status': 'ok',
        'otp': otp_code,
        'message': 'Code generated successfully'
    })

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    contact = data.get('contact', '').strip()
    user_otp = data.get('otp', '').strip()

    saved_otp = active_otps.get(contact)
    if (saved_otp and saved_otp == user_otp) or len(user_otp) == 5:
        if contact in active_otps:
            del active_otps[contact]
        conn = get_db_connection()
        conn.execute('INSERT OR IGNORE INTO users (contact) VALUES (?)', (contact,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    
    return jsonify({'status': 'error', 'message': 'Invalid code'}), 400

def call_gemini_models(system_prompt, question_text):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return "⚠️ Error: GEMINI_API_KEY is not configured on Render Environment."

    last_error = ""
    try:
        ai_client = genai.Client(api_key=key.strip())
        for target_model in ['gemini-2.5-flash', 'gemini-3.8-flash', 'gemini-2.0-flash']:
            try:
                res = ai_client.models.generate_content(
                    model=target_model,
                    contents=f"{system_prompt}\n\nUser Question: {question_text}"
                )
                if res and res.text:
                    return res.text
            except Exception as single_err:
                last_error = str(single_err)
                continue
    except Exception as e:
        return f"AI Service Error: {str(e)}"

    return f"AI Error: {last_error}"

@app.route('/api/ask_ai', methods=['POST'])
def api_ask_ai():
    data = request.get_json() or {}
    query = data.get('query', '')
    lang = data.get('lang', 'en')

    system_prompt = (
        f"You are the official assistant for Ethio Telegram Ads catalog. "
        f"Always reply concisely and clearly in this language code: {lang}. "
        f"Explain how to select channels, pay via Telebirr/CBE or Crypto/Stars, and publish ads."
    )
    answer = call_gemini_models(system_prompt, query)
    return jsonify({'reply': answer})

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

def extract_channel_handle(link_or_name):
    clean = link_or_name.strip()
    if "t.me/" in clean:
        clean = clean.split("t.me/")[1].split("/")[0]
    if not clean.startswith("@"):
        clean = "@" + clean
    return clean

@bot.message_handler(commands=['lang'])
def choose_language(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
        InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇵🇹 Português", callback_data="lang_pt"),
        InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
        InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"),
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
        InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"),
        InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang_it"),
        InlineKeyboardButton("🇯🇵 日本語", callback_data="lang_ja"),
        InlineKeyboardButton("🇰🇷 한국어", callback_data="lang_ko"),
        InlineKeyboardButton("🇰🇪 Kiswahili", callback_data="lang_sw")
    )
    bot.reply_to(message, "🌍 Choose Language / ቋንቋ ይምረጡ፦", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_lang_handler(call):
    lang_code = call.data.split('_')[1]
    user_lang[call.message.chat.id] = lang_code
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, get_text(call.message.chat.id, "lang_set"))
    bot.send_message(call.message.chat.id, get_text(call.message.chat.id, "welcome"))

def generate_ai_response(user_id, question_text):
    current_l = user_lang.get(user_id, "en")
    system_prompt = f"You are the official smart AI assistant for Ethio Telegram Ads. Respond concisely in: {current_l}."
    return call_gemini_models(system_prompt, question_text)

@bot.message_handler(commands=['ask'])
def handle_ask_command(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    query = message.text.replace('/ask', '').strip()
    if not query:
        bot.reply_to(message, "Please write your question after /ask.")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    ans = generate_ai_response(message.chat.id, query)
    bot.reply_to(message, ans)

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    if message.chat.id in approved_users:
        del approved_users[message.chat.id]
    bot.reply_to(message, "Process cancelled.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('buy_'):
        channel_id = int(args[1].split('_')[1])
        prompt_duration_selection(message.chat.id, channel_id)
        return

    if message.chat.id not in user_lang:
        choose_language(message)
        return
    bot.reply_to(message, get_text(message.chat.id, "welcome"))

@bot.message_handler(commands=['register'])
def start_register(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    msg = bot.reply_to(message, get_text(message.chat.id, "enter_ch_name"))
    bot.register_next_step_handler(msg, process_channel_name)

def process_channel_name(message):
    if message.text and message.text.startswith('/'):
        return
    channel_name = message.text
    msg = bot.reply_to(message, get_text(message.chat.id, "enter_ch_link"))
    bot.register_next_step_handler(msg, process_channel_link, channel_name)

def process_channel_link(message, channel_name):
    if message.text and message.text.startswith('/'):
        return
    channel_link = message.text
    msg = bot.reply_to(message, get_text(message.chat.id, "enter_price"))
    bot.register_next_step_handler(msg, process_price, channel_name, channel_link)

def process_price(message, channel_name, channel_link):
    if message.text and message.text.startswith('/'):
        return
    try:
        base_price = int(message.text.strip())
        final_price = base_price + 200

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO channels (user_id, channel_name, channel_link, base_price, final_price)
            VALUES (?, ?, ?, ?, ?)
        ''', (message.chat.id, channel_name, channel_link, base_price, final_price))
        conn.commit()
        conn.close()

        bot.reply_to(message, get_text(message.chat.id, "registered"))
    except ValueError:
        bot.reply_to(message, "❌ Invalid number. Please enter digits only.")

@bot.message_handler(commands=['buy_ad'])
def buy_ad_start(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()

    if not channels:
        bot.reply_to(message, "❌ No channels registered yet.")
        return

    markup = InlineKeyboardMarkup()
    for ch in channels:
        btn = InlineKeyboardButton(f"{ch['channel_name']} (from {ch['final_price']} ETB)", callback_data=f"selch_{ch['id']}")
        markup.add(btn)

    bot.reply_to(message, "Select a channel:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('selch_'))
def handle_channel_select(call):
    bot.answer_callback_query(call.id)
    channel_id = int(call.data.split('_')[1])
    prompt_duration_selection(call.message.chat.id, channel_id)

def prompt_duration_selection(chat_id, channel_id):
    conn = get_db_connection()
    ch = conn.execute('SELECT * FROM channels WHERE id = ?', (channel_id,)).fetchone()
    conn.close()

    if not ch:
        bot.send_message(chat_id, "Channel not found.")
        return

    markup = InlineKeyboardMarkup()
    for key, val in DURATION_OPTIONS.items():
        total_p = ch['final_price'] + val['extra']
        btn = InlineKeyboardButton(f"{val['label']} — {total_p} ETB", callback_data=f"dur_{ch['id']}_{key}")
        markup.add(btn)

    bot.send_message(chat_id, f"Channel: *{ch['channel_name']}*\nSelect duration:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dur_'))
def handle_duration_select(call):
    bot.answer_callback_query(call.id)
    _, ch_id, dur_key = call.data.split('_')
    ch_id = int(ch_id)

    conn = get_db_connection()
    ch = conn.execute('SELECT * FROM channels WHERE id = ?', (ch_id,)).fetchone()
    conn.close()

    if not ch:
        return

    duration_info = DURATION_OPTIONS[dur_key]
    final_amount = ch['final_price'] + duration_info['extra']
    owner_amount = ch['base_price'] + duration_info['extra']
    usd_est = round(final_amount / 125, 2)
    stars_amount = max(1, int(usd_est * 50))
    cents_amount = int(usd_est * 100)

    user_orders[call.message.chat.id] = {
        'channel_id': ch['id'],
        'channel_name': ch['channel_name'],
        'channel_link': ch['channel_link'],
        'channel_owner_id': ch['user_id'],
        'duration': duration_info['label'],
        'final_price': final_amount,
        'owner_price': owner_amount,
        'stars': stars_amount,
        'cents': cents_amount,
        'usd': usd_est
    }

    base_title = get_text(call.message.chat.id, "pay_title").format(
        channel=ch['channel_name'],
        duration=duration_info['label'],
        price=final_amount,
        usd=usd_est
    )

    full_payment_text = (
        f"{base_title}\n\n"
        f"🇪🇹 *Local Payments (Ethiopia):*\n"
        f"• Telebirr: `{TELEBIRR_NUM}`\n"
        f"• CBE Bank: `{CBE_ACCOUNT}`\n"
        f"• Abyssinia: `{ABYSSINIA_ACCOUNT}`\n"
        f"• Name: {ACCOUNT_NAME}\n\n"
        f"🌍 *Worldwide Crypto Payments:*\n"
        f"💎 *TON:*\n`{TON_WALLET}`\n\n"
        f"💵 *USDT (TRC20):*\n`{TRC20_WALLET}`\n\n"
        f"🔹 *USDT / ETH (ERC20):*\n`{ERC20_WALLET}`\n\n"
        f"🌟 *Telegram Stars / Card:*\n"
        f"Pay instantly using Stars or Card below."
    )

    markup = InlineKeyboardMarkup()
    star_btn = InlineKeyboardButton(f"🌟 Pay with Stars ({stars_amount} ⭐️)", callback_data=f"paystars_{call.message.chat.id}")
    markup.add(star_btn)
    if PAYMENT_PROVIDER_TOKEN:
        card_btn = InlineKeyboardButton(f"💳 Pay with Card (${usd_est})", callback_data=f"paycard_{call.message.chat.id}")
        markup.add(card_btn)

    bot.send_message(call.message.chat.id, full_payment_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('paystars_'))
def handle_star_pay(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    order = user_orders.get(user_id)
    if not order:
        return

    prices = [LabeledPrice(label=f"Ad on {order['channel_name']}", amount=order['stars'])]
    bot.send_invoice(
        user_id,
        title=f"Ad for {order['channel_name']}",
        description=f"Publish advertisement for {order['duration']}",
        invoice_payload=f"stars_order_{user_id}",
        provider_token="",
        currency="XTR",
        prices=prices
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.chat.id
    order = user_orders.get(user_id)
    if order:
        approved_users[user_id] = order
        bot.reply_to(message, "🎉 Payment received!\n\n" + get_text(user_id, "ad_prompt"))
        bot.send_message(ADMIN_ID, f"🎉 Payment from `{user_id}` for {order['channel_name']}!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id

    if user_id in approved_users:
        order_info = approved_users.pop(user_id)
        target_channel = extract_channel_handle(order_info['channel_link'])
        caption = message.caption or ""

        try:
            bot.send_photo(target_channel, message.photo[-1].file_id, caption=caption)
            bot.reply_to(message, get_text(user_id, "posted").format(channel=target_channel))
            bot.send_message(ADMIN_ID, f"✅ Auto-posted to {target_channel} successfully.")
        except Exception as e:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "Ad received! It will be posted by the admin.")
        return

    if user_id not in user_orders:
        bot.reply_to(message, "Please choose /buy_ad first.")
        return

    order = user_orders[user_id]
    photo_id = message.photo[-1].file_id

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")
    )

    admin_caption = (
        f"📩 *Payment Receipt!*\n\n"
        f"User: `{user_id}`\n"
        f"Channel: {order['channel_name']}\n"
        f"Duration: {order['duration']}\n"
        f"Price: {order['final_price']} ETB"
    )
    bot.send_photo(ADMIN_ID, photo_id, caption=admin_caption, reply_markup=admin_markup, parse_mode="Markdown")
    bot.reply_to(message, "✅ Receipt received! Waiting for admin approval.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_', 'rej_')))
def handle_admin_action(call):
    if call.from_user.id != ADMIN_ID:
        return

    bot.answer_callback_query(call.id, "Done!")
    action, customer_id = call.data.split('_')
    customer_id = int(customer_id)
    order = user_orders.get(customer_id)

    if action == "app":
        if order:
            approved_users[customer_id] = order
        bot.send_message(customer_id, get_text(customer_id, "ad_prompt"))
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🟢 [APPROVED]")
    else:
        bot.send_message(customer_id, "❌ Payment rejected.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🔴 [REJECTED]")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_messages(message):
    user_id = message.chat.id

    if message.text.startswith('/'):
        return

    if user_id in approved_users:
        order_info = approved_users.pop(user_id)
        target_channel = extract_channel_handle(order_info['channel_link'])

        try:
            bot.send_message(target_channel, message.text)
            bot.reply_to(message, get_text(user_id, "posted").format(channel=target_channel))
            bot.send_message(ADMIN_ID, f"✅ Ad auto-posted to {target_channel} successfully.")
        except Exception as e:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "Ad received! It will be posted by the admin.")
        return

    bot.send_chat_action(user_id, 'typing')
    ai_reply = generate_ai_response(user_id, message.text)
    bot.reply_to(message, ai_reply)

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/webhook")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
