import os
import sqlite3
import threading
from flask import Flask, jsonify
from flask_cors import CORS
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)
CORS(app)

# የቦት እና የአድሚን መረጃዎች
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6179388927
CBE_ACCOUNT = "1000785625556"
TELEBIRR_NUM = "0927943402"
ABYSSINIA_ACCOUNT = "218988407"
ACCOUNT_NAME = "Wo..."

bot = telebot.TeleBot(BOT_TOKEN)

# ጊዜያዊ የትዕዛዝ መያዣ
user_orders = {}

def get_db_connection():
    conn = sqlite3.connect('ads.db')
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
    return "Ethio Ad Bot is Running Live!"

# /start ትዕዛዝ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "እንኳን ደህና መጡ! 📢\n\n"
        "• ቻናልዎን ለማስመዝገብ፦ /register\n"
        "• ማስታወቂያ ለማዘዝ፦ /buy_ad\n"
        "• ሙሉ የቻናሎች ዝርዝር በዌብሳይት ለመመልከት ከታች ያለውን ቁልፍ ይጠቀሙ።"
    )
    bot.reply_to(message, text)

# ----------------- ቻናል ምዝገባ -----------------
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
            f"💰 የሚቀርብበት ዋጋ፦ {final_price} ብር / 24 ሰዓት\n\n"
            f"ማስታወቂያ ሲታዘዝ በቦቱ በኩል መልእክት ይደርስዎታል!"
        )
        bot.reply_to(message, success_text)
    except ValueError:
        bot.reply_to(message, "❌ ዋጋውን በቁጥር ብቻ ያስገቡ። እንደገና /register ብለው ይሞክሩ።")

# ----------------- ማስታወቂያ ማዘዝ እና ክፍያ -----------------
@bot.message_handler(commands=['buy_ad'])
def buy_ad_start(message):
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()

    if not channels:
        bot.reply_to(message, "❌ በአሁኑ ሰዓት የተመዘገበ ቻናል የለም።")
        return

    markup = InlineKeyboardMarkup()
    for ch in channels:
        btn = InlineKeyboardButton(f"{ch['channel_name']} - {ch['final_price']} ብር", callback_data=f"buy_{ch['id']}")
        markup.add(btn)

    bot.reply_to(message, "ማስታወቂያ ማስተላለፍ የሚፈልጉበትን ቻናል ይምረጡ፦", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_ad_selection(call):
    channel_id = int(call.data.split('_')[1])
    conn = get_db_connection()
    ch = conn.execute('SELECT * FROM channels WHERE id = ?', (channel_id,)).fetchone()
    conn.close()

    if not ch:
        bot.answer_callback_query(call.id, "ቻናሉ አልተገኘም!")
        return

    user_orders[call.message.chat.id] = {
        'channel_id': ch['id'],
        'channel_name': ch['channel_name'],
        'channel_owner_id': ch['user_id'],
        'final_price': ch['final_price'],
        'base_price': ch['base_price']
    }

    msg_text = (
        f"💳 *የክፍያ መመሪያ*\n\n"
        f"📢 *የተመረጠው ቻናል፦* {ch['channel_name']}\n"
        f"💰 *የሚከፈለው ጠቅላላ ዋጋ፦* {ch['final_price']} ብር\n\n"
        f"የክፍያ አማራጮች፦\n"
        f"📱 *Telebirr፦* `{TELEBIRR_NUM}`\n"
        f"🏦 *የኢትዮጵያ ንግድ ባንክ (CBE)፦* `{CBE_ACCOUNT}`\n"
        f"🏛 *አቢሲኒያ ባንክ (BOA)፦* `{ABYSSINIA_ACCOUNT}`\n"
        f"👤 *ስም፦* {ACCOUNT_NAME}\n\n"
        f"⚠️ *ማሳሰቢያ፦* ክፍያውን ከፈጸሙ በኋላ የደረሰኙን ስክሪንሾት (Screenshot/ፎቶ) ለዚህ ቦት ይላኩ።"
    )
    bot.send_message(call.message.chat.id, msg_text, parse_mode="Markdown")

# ደረሰኝ (ፎቶ) ሲላክ
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.chat.id
    if user_id not in user_orders:
        bot.reply_to(message, "እባክዎ መጀመሪያ /buy_ad ብለው ማስታወቂያ የሚያዙበትን ቻናል ይምረጡ።")
        return

    order = user_orders[user_id]
    photo_id = message.photo[-1].file_id

    # ለአድሚኑ (ለእርስዎ) የሚላክ ማረጋገጫ
    admin_markup = InlineKeyboardMarkup()
    approve_btn = InlineKeyboardButton("✅ አጽድቅ (Approve)", callback_data=f"app_{user_id}")
    reject_btn = InlineKeyboardButton("❌ ሰርዝ (Reject)", callback_data=f"rej_{user_id}")
    admin_markup.add(approve_btn, reject_btn)

    admin_caption = (
        f"📩 *አዲስ የክፍያ ደረሰኝ ደርሷል!*\n\n"
        f"👤 *የከፋይ ID፦* `{user_id}`\n"
        f"📢 *ቻናል፦* {order['channel_name']}\n"
        f"💰 *ጠቅላላ የተከፈለው፦* {order['final_price']} ብር\n"
        f"💵 *ለእርስዎ የሚቀረው ኮሚሽን፦* 200 ብር\n"
        f"📲 *ለቻናሉ ባለቤት የሚተላለፈው፦* {order['base_price']} ብር"
    )

    bot.send_photo(ADMIN_ID, photo_id, caption=admin_caption, reply_markup=admin_markup, parse_mode="Markdown")
    bot.reply_to(message, "✅ ደረሰኝዎ ደርሶናል! ክፍያው በአድሚን ተረጋግጦ በቅርቡ ይጸድቃል።")

# አድሚን ማጽደቅ ወይም መሰረዝ ሲጫን
@bot.callback_query_handler(func=lambda call: call.data.startswith(('app_', 'rej_')))
def handle_admin_action(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "ይህንን ማድረግ የሚችሉት አድሚኑ ብቻ ናቸው!")
        return

    action, customer_id = call.data.split('_')
    customer_id = int(customer_id)

    order = user_orders.get(customer_id)

    if action == "app":
        bot.send_message(customer_id, "🎉 ክፍያዎ ተረጋግጦ ጸድቋል! እባክዎ እንዲለጠፍ የሚፈልጉትን የማስታወቂያ ጽሑፍ/ፎቶ እዚህ ይላኩ።")
        if order:
            bot.send_message(order['channel_owner_id'], f"📢 ማስታወቂያ ተገዝቷል!\nቻናልዎ፦ {order['channel_name']}\nየእርስዎ ክፍያ ({order['base_price']} ብር) ማስታወቂያው እንደተለጠፈ የሚተላለፍ ይሆናል።")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🟢 [ክፍያው ጸድቋል]")
    else:
        bot.send_message(customer_id, "❌ ክፍያዎ አልተረጋገጠም ወይም ውድቅ ተደርጓል። እባክዎ ትክክለኛውን ደረሰኝ በድጋሚ ይላኩ።")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🔴 [ውድቅ ተደርጓል]")

    bot.answer_callback_query(call.id, "ተጠናቋል!")

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
