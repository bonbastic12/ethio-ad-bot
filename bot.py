import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Update

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6179388927
CBE_ACCOUNT = "1000785625556"
TELEBIRR_NUM = "0927943402"
ABYSSINIA_ACCOUNT = "218988407"
ACCOUNT_NAME = "Wo..."
RENDER_URL = "https://ethio-ad-bot-wz6h.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

DURATION_OPTIONS = {
    "24h": {"label": "24 ሰዓት (1 ቀን)", "extra": 0},
    "48h": {"label": "48 ሰዓት (2 ቀናት)", "extra": 300},
    "1w":  {"label": "1 ሳምንት (7 ቀናት)", "extra": 600},
    "2w":  {"label": "2 ሳምንታት (14 ቀናት)", "extra": 900},
    "1m":  {"label": "1 ወር (30 ቀናት)", "extra": 1200},
    "2m":  {"label": "2 ወራት (60 ቀናት)", "extra": 1500}
}

user_orders = {}
approved_users = {}

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
    conn.commit()
    conn.close()

init_db()

@app.route('/api/channels', methods=['GET'])
def get_channels():
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()
    return jsonify([dict(row) for row in channels])

@app.route('/')
def home():
    return "Ethio Ad Bot is Running Fast & Live!", 200

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

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    if message.chat.id in approved_users:
        del approved_users[message.chat.id]
    bot.reply_to(message, "የነበረው ሂደት ተሰርዟል። አዲስ ትዕዛዝ ለመጀመር /start፣ /register ወይም /buy_ad ይጠቀሙ።")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("buy_"):
        try:
            channel_id = int(args[1].split("_")[1])
            prompt_duration_selection(message.chat.id, channel_id)
            return
        except Exception:
            pass

    text = (
        "እንኳን ደህና መጡ! 📢\n\n"
        "• ቻናልዎን ለማስመዝገብ፦ /register\n"
        "• ማስታወቂያ ለማዘዝ፦ /buy_ad\n"
        "• የነበረውን ለመሰረዝ፦ /cancel"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['register'])
def start_register(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    msg = bot.reply_to(message, "እባክዎ የቻናልዎን ስም ያስገቡ (ለምሳሌ፦ MR ODDS):")
    bot.register_next_step_handler(msg, process_channel_name)

def process_channel_name(message):
    if message.text and message.text.startswith('/'):
        return
    channel_name = message.text
    msg = bot.reply_to(message, "የቻናሉን ሊንክ ያስገቡ (ለምሳሌ፦ https://t.me/wodtech1):")
    bot.register_next_step_handler(msg, process_channel_link, channel_name)

def process_channel_link(message, channel_name):
    if message.text and message.text.startswith('/'):
        return
    channel_link = message.text
    msg = bot.reply_to(message, "የሚፈልጉትን የመነሻ (የ24 ሰዓት) ዋጋ በብር ብቻ ያስገቡ (ለምሳሌ፦ 1000):")
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

        success_text = (
            f"✅ ቻናልዎ በተሳካ ሁኔታ ተመዝግቧል!\n\n"
            f"📢 ቻናል፦ {channel_name}\n"
            f"💰 የመነሻ ዋጋ (24 ሰዓት)፦ {final_price} ብር\n\n"
            f"ማስታወቂያ ሲታዘዝ በቦቱ በኩል መልእክት ይደርስዎታል!"
        )
        bot.reply_to(message, success_text)
    except ValueError:
        bot.reply_to(message, "❌ ዋጋውን በቁጥር ብቻ ያስገቡ። እንደገና /register ብለው ይሞክሩ።")

@bot.message_handler(commands=['buy_ad'])
def buy_ad_start(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()

    if not channels:
        bot.reply_to(message, "❌ በአሁኑ ሰዓት የተመዘገበ ቻናል የለም። እባክዎ አስቀድመው በ /register ይመዝግቡ።")
        return

    markup = InlineKeyboardMarkup()
    for ch in channels:
        btn = InlineKeyboardButton(f"{ch['channel_name']} (ከ {ch['final_price']} ብር ጀምሮ)", callback_data=f"selch_{ch['id']}")
        markup.add(btn)

    bot.reply_to(message, "ማስታወቂያ ማስተላለፍ የሚፈልጉበትን ቻናል ይምረጡ፦", reply_markup=markup)

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
        bot.send_message(chat_id, "ቻናሉ አልተገኘም! እባክዎ እንደገና /buy_ad ብለው ይሞክሩ።")
        return

    markup = InlineKeyboardMarkup()
    for key, val in DURATION_OPTIONS.items():
        total_p = ch['final_price'] + val['extra']
        btn = InlineKeyboardButton(f"{val['label']} — {total_p} ብር", callback_data=f"dur_{ch['id']}_{key}")
        markup.add(btn)

    bot.send_message(chat_id, f"📢 ለቻናል፦ *{ch['channel_name']}*\nየማስታወቂያውን የቆይታ ጊዜ ይምረጡ፦", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dur_'))
def handle_duration_select(call):
    bot.answer_callback_query(call.id)
    _, ch_id, dur_key = call.data.split('_')
    ch_id = int(ch_id)

    conn = get_db_connection()
    ch = conn.execute('SELECT * FROM channels WHERE id = ?', (ch_id,)).fetchone()
    conn.close()

    if not ch:
        bot.send_message(call.message.chat.id, "ቻናሉ አልተገኘም! እባክዎ እንደገና /buy_ad ብለው ይሞክሩ።")
        return

    duration_info = DURATION_OPTIONS[dur_key]
    final_amount = ch['final_price'] + duration_info['extra']
    owner_amount = ch['base_price'] + duration_info['extra']

    user_orders[call.message.chat.id] = {
        'channel_id': ch['id'],
        'channel_name': ch['channel_name'],
        'channel_link': ch['channel_link'],
        'channel_owner_id': ch['user_id'],
        'duration': duration_info['label'],
        'final_price': final_amount,
        'owner_price': owner_amount
    }

    msg_text = (
        f"💳 *የክፍያ መመሪያ*\n\n"
        f"📢 *ቻናል፦* {ch['channel_name']}\n"
        f"⏳ *የቆይታ ጊዜ፦* {duration_info['label']}\n"
        f"💰 *ጠቅላላ ክፍያ፦* {final_amount} ብር\n\n"
        f"የክፍያ አማራጮች፦\n"
        f"📱 *Telebirr፦* `{TELEBIRR_NUM}`\n"
        f"🏦 *የኢትዮጵያ ንግድ ባንክ (CBE)፦* `{CBE_ACCOUNT}`\n"
        f"🏛 *አቢሲኒያ ባንክ (BOA)፦* `{ABYSSINIA_ACCOUNT}`\n"
        f"👤 *ስም፦* {ACCOUNT_NAME}\n\n"
        f"⚠️ *ማሳሰቢያ፦* ክፍያውን ከፈጸሙ በኋላ የደረሰኙን ስክሪንሾት (Screenshot/ፎቶ) ለዚህ ቦት ይላኩ።"
    )
    bot.send_message(call.message.chat.id, msg_text, parse_mode="Markdown")

# ፎቶ ሲላክ (ደረሰኝ ወይም ማስታወቂያ)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id

    # ደንበኛው ክፍያው ከጸደቀ በኋላ የፎቶ ማስታወቂያ ሲልክ
    if user_id in approved_users:
        order_info = approved_users.pop(user_id)
        target_channel = extract_channel_handle(order_info['channel_link'])
        caption = message.caption or ""

        try:
            bot.send_photo(target_channel, message.photo[-1].file_id, caption=caption)
            bot.reply_to(message, f"🎉 ማስታወቂያዎ በቀጥታ በ {target_channel} ቻናል ላይ በተሳካ ሁኔታ ተለጥፏል!")
            bot.send_message(ADMIN_ID, f"✅ ማስታወቂያው በ {target_channel} ቻናል ላይ በራስ-ሰር ተለጥፏል።")
        except Exception as e:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "ማስታወቂያዎ ደርሷል! አድሚኑ በቅርቡ ቻናሉ ላይ ይለጥፈዋል።")
            bot.send_message(ADMIN_ID, f"⚠️ ማስታወቂያውን በራስ-ሰር መለጠፍ አልተቻለም (ቦቱ በቻናሉ ላይ Admin መሆኑን ያረጋግጡ)። ስህተት፦ {e}")
        return

    # የደረሰኝ ፎቶ ሲልክ
    if user_id not in user_orders:
        bot.reply_to(message, "እባክዎ መጀመሪያ /buy_ad ብለው ማስታወቂያ የሚያዙበትን ቻናል እና ጊዜ ይምረጡ።")
        return

    order = user_orders[user_id]
    photo_id = message.photo[-1].file_id

    admin_markup = InlineKeyboardMarkup()
    approve_btn = InlineKeyboardButton("✅ አጽድቅ (Approve)", callback_data=f"app_{user_id}")
    reject_btn = InlineKeyboardButton("❌ ሰርዝ (Reject)", callback_data=f"rej_{user_id}")
    admin_markup.add(approve_btn, reject_btn)

    admin_caption = (
        f"📩 *አዲስ የክፍያ ደረሰኝ!*\n\n"
        f"👤 *የከፋይ ID፦* `{user_id}`\n"
        f"📢 *ቻናል፦* {order['channel_name']}\n"
        f"⏳ *ቆይታ፦* {order['duration']}\n"
        f"💰 *ጠቅላላ የተከፈለው፦* {order['final_price']} ብር\n"
        f"💵 *ለእርስዎ ኮሚሽን፦* 200 ብር\n"
        f"📲 *ለቻናሉ ባለቤት የሚተላለፍ፦* {order['owner_price']} ብር"
    )

    bot.send_photo(ADMIN_ID, photo_id, caption=admin_caption, reply_markup=admin_markup, parse_mode="Markdown")
    bot.reply_to(message, "✅ ደረሰኝዎ ደርሶናል! ክፍያው በአድሚን ተረጋግጦ በቅርቡ ይጸድቃል።")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_', 'rej_')))
def handle_admin_action(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "ይህንን ማድረግ የሚችሉት አድሚኑ ብቻ ናቸው!")
        return

    bot.answer_callback_query(call.id, "ተጠናቋል!")
    action, customer_id = call.data.split('_')
    customer_id = int(customer_id)
    order = user_orders.get(customer_id)

    if action == "app":
        if order:
            approved_users[customer_id] = order
        bot.send_message(customer_id, "🎉 ክፍያዎ ተረጋግጦ ጸድቋል! እባክዎ በቻናሉ ላይ እንዲለጠፍ የሚፈልጉትን የማስታወቂያ ጽሑፍ ወይም ፎቶ እዚህ ይላኩ።")
        if order:
            bot.send_message(
                order['channel_owner_id'],
                f"📢 ማስታወቂያ ተገዝቷል!\nቻናል፦ {order['channel_name']}\nቆይታ፦ {order['duration']}\nክፍያዎ፦ {order['owner_price']} ብር"
            )
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🟢 [ክፍያው ጸድቋል]")
    else:
        bot.send_message(customer_id, "❌ ክፍያዎ አልተረጋገጠም ወይም ውድቅ ተደርጓል። እባክዎ ትክክለኛውን ደረሰኝ በድጋሚ ይላኩ።")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🔴 [ውድቅ ተደርጓል]")

# የጽሑፍ ማስታወቂያ ሲላክ
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_ad(message):
    user_id = message.chat.id

    if message.text.startswith('/'):
        return

    # ደንበኛው ክፍያው ከጸደቀ በኋላ የጽሑፍ ማስታወቂያ ሲልክ
    if user_id in approved_users:
        order_info = approved_users.pop(user_id)
        target_channel = extract_channel_handle(order_info['channel_link'])

        try:
            bot.send_message(target_channel, message.text)
            bot.reply_to(message, f"🎉 የማስታወቂያ ጽሑፍዎ በቀጥታ በ {target_channel} ቻናል ላይ በተሳካ ሁኔታ ተለጥፏል!")
            bot.send_message(ADMIN_ID, f"✅ ማስታወቂያው በ {target_channel} ቻናል ላይ በራስ-ሰር ተለጥፏል።")
        except Exception as e:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "የማስታወቂያ ጽሑፍዎ ደርሷል! አድሚኑ በቅርቡ ቻናሉ ላይ ይለጥፈዋል።")
            bot.send_message(ADMIN_ID, f"⚠️ ማስታወቂያውን በራስ-ሰር መለጠፍ አልተቻለም (ቦቱ በቻናሉ ላይ Admin መሆኑን ያረጋግጡ)። ስህተት፦ {e}")
        return

    bot.reply_to(message, "ትዕዛዝ ለመጀመር /start፣ /buy_ad ወይም /register ይጠቀሙ።")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/webhook")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
