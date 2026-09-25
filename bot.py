import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, LabeledPrice
from google import genai

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "") # ለ Card / Google Pay (ከ @BotFather የሚገኝ)
ADMIN_ID = 6179388927

# የሀገር ውስጥ ክፍያ
CBE_ACCOUNT = "1000785625556"
TELEBIRR_NUM = "0927943402"
ABYSSINIA_ACCOUNT = "218988407"
ACCOUNT_NAME = "Wo..."

# ዓለም አቀፍ የክሪፕቶ ዋሌቶች
TON_WALLET = "UQCxUAhKH0Zlj_LT2-fDtktqVZ7sFsLNS47-pfqOK_MiOjnm"
TRC20_WALLET = "TSTAsyXoWR8CqWLP2yGaFgJ385vJs2WeR8"
ERC20_WALLET = "0x8929FF9b5cE44E4c433318D6321AFF2c077Ed9DF"

RENDER_URL = "https://ethio-ad-bot-wz6h.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 7 ቋንቋዎች
LANG_STRINGS = {
    "am": {
        "welcome": "እንኳን ደህና መጡ! 📢\n\n• ቻናል ለመመዝገብ፦ /register\n• ማስታወቂያ ለመግዛት፦ /buy_ad\n• ቋንቋ ለመቀየር፦ /lang\n• የነበረውን ለመሰረዝ፦ /cancel\n\nለማንኛውም ጥያቄ በቀጥታ ጽፈው ማነጋገር ይችላሉ (AI Assistant ዝግጁ ነው)።",
        "lang_set": "ቋንቋው ወደ አማርኛ ተቀይሯል።",
        "enter_ch_name": "እባክዎ የቻናልዎን ስም ያስገቡ (ለምሳሌ፦ MR ODDS):",
        "enter_ch_link": "የቻናሉን ሊንክ ያስገቡ (ለምሳሌ፦ https://t.me/wodtech1):",
        "enter_price": "የሚፈልጉትን የመነሻ ዋጋ በብር ያስገቡ (ለምሳሌ፦ 1000):",
        "registered": "✅ ቻናልዎ በተሳካ ሁኔታ ተመዝግቧል!",
        "pay_title": "💳 *የክፍያ መመሪያ*\n\n📢 *ቻናል፦* {channel}\n⏳ *ቆይታ፦* {duration}\n💰 *ዋጋ፦* {price} ETB (ወይም ~{usd}$ USD)",
        "ad_prompt": "🎉 ክፍያዎ ጸድቋል! እባክዎ በቻናሉ እንዲለጠፍ የሚፈልጉትን ማስታወቂያ (ጽሑፍ ወይም ፎቶ) እዚህ ይላኩ።",
        "posted": "🎉 ማስታወቂያዎ በቀጥታ በ {channel} ቻናል ላይ በተሳካ ሁኔታ ተለጥፏል!"
    },
    "en": {
        "welcome": "Welcome! 📢\n\n• Register channel: /register\n• Buy ad: /buy_ad\n• Change language: /lang\n• Cancel: /cancel\n\nAsk any question directly; our AI assistant is ready to help.",
        "lang_set": "Language switched to English.",
        "enter_ch_name": "Please enter your channel name:",
        "enter_ch_link": "Please enter channel link (e.g. https://t.me/wodtech1):",
        "enter_price": "Enter starting price in ETB (e.g. 1000):",
        "registered": "✅ Your channel has been registered successfully!",
        "pay_title": "💳 *Payment Instructions*\n\n📢 *Channel:* {channel}\n⏳ *Duration:* {duration}\n💰 *Total:* {price} ETB (or ~{usd}$ USD)",
        "ad_prompt": "🎉 Payment approved! Please send the ad text or photo to be published.",
        "posted": "🎉 Your ad has been published to {channel} successfully!"
    },
    "fr": {
        "welcome": "Bienvenue! 📢\n\n• Enregistrer: /register\n• Acheter pub: /buy_ad\n• Langue: /lang\n• Annuler: /cancel\n\nPosez votre question à notre assistant IA.",
        "lang_set": "Langue changée en Français.",
        "enter_ch_name": "Entrez le nom de votre chaîne:",
        "enter_ch_link": "Entrez le lien de la chaîne:",
        "enter_price": "Entrez le prix de base en ETB:",
        "registered": "✅ Votre chaîne est enregistrée avec succès!",
        "pay_title": "💳 *Instructions de paiement*\n\n📢 *Chaîne:* {channel}\n⏳ *Durée:* {duration}\n💰 *Total:* {price} ETB (ou ~{usd}$ USD)",
        "ad_prompt": "🎉 Paiement approuvé! Envoyez votre texte publicitaire ou photo.",
        "posted": "🎉 Publicité publiée sur {channel} avec succès!"
    },
    "ru": {
        "welcome": "Добро пожаловать! 📢\n\n• Добавить канал: /register\n• Купить рекламу: /buy_ad\n• Язык: /lang\n• Отмена: /cancel\n\nЗадайте вопрос нашему ИИ-помощнику.",
        "lang_set": "Язык изменен на Русский.",
        "enter_ch_name": "Введите название канала:",
        "enter_ch_link": "Введите ссылку на канал:",
        "enter_price": "Введите базовую цену в ETB:",
        "registered": "✅ Канал успешно добавлен!",
        "pay_title": "💳 *Оплата рекламы*\n\n📢 *Канал:* {channel}\n⏳ *Срок:* {duration}\n💰 *Сумма:* {price} ETB (или ~{usd}$ USD)",
        "ad_prompt": "🎉 Оплата подтверждена! Отправьте текст или фото рекламы.",
        "posted": "🎉 Реклама успешно опубликована в {channel}!"
    },
    "es": {
        "welcome": "¡Bienvenido! 📢\n\n• Registrar canal: /register\n• Comprar anuncio: /buy_ad\n• Cambiar idioma: /lang\n• Cancelar: /cancel\n\nPuede consultar cualquier duda con nuestro asistente IA.",
        "lang_set": "Idioma cambiado a Español.",
        "enter_ch_name": "Ingrese el nombre del canal:",
        "enter_ch_link": "Ingrese el enlace del canal:",
        "enter_price": "Ingrese el precio base en ETB:",
        "registered": "✅ ¡Canal registrado con éxito!",
        "pay_title": "💳 *Instrucciones de pago*\n\n📢 *Canal:* {channel}\n⏳ *Duración:* {duration}\n💰 *Total:* {price} ETB (o ~{usd}$ USD)",
        "ad_prompt": "🎉 ¡Pago aprobado! Envíe el texto o la imagen de su anuncio.",
        "posted": "🎉 ¡Anuncio publicado en {channel} con éxito!"
    },
    "pt": {
        "welcome": "Bem-vindo! 📢\n\n• Registrar canal: /register\n• Comprar anúncio: /buy_ad\n• Mudar idioma: /lang\n• Cancelar: /cancel\n\nFale com nosso assistente de IA a qualquer momento.",
        "lang_set": "Idioma alterado para Português.",
        "enter_ch_name": "Digite o nome do canal:",
        "enter_ch_link": "Digite o link do canal:",
        "enter_price": "Digite o preço base em ETB:",
        "registered": "✅ Canal registrado com sucesso!",
        "pay_title": "💳 *Instruções de pagamento*\n\n📢 *Canal:* {channel}\n⏳ *Duração:* {duration}\n💰 *Total:* {price} ETB (ou ~{usd}$ USD)",
        "ad_prompt": "🎉 Pagamento aprovado! Envie o texto ou a foto do anúncio.",
        "posted": "🎉 Anúncio publicado em {channel} com sucesso!"
    },
    "ar": {
        "welcome": "أهلاً بك! 📢\n\n• تسجيل قناة: /register\n• شراء إعلان: /buy_ad\n• تغيير اللغة: /lang\n• إلغاء: /cancel\n\nيمكنك التحدث مع المساعد الذكي بأي وقت.",
        "lang_set": "تم تغيير اللغة إلى العربية.",
        "enter_ch_name": "يرجى إدخال اسم القناة:",
        "enter_ch_link": "يرجى إدخال رابط القناة:",
        "enter_price": "أدخل السعر الأساسي بالـ ETB:",
        "registered": "✅ تم تسجيل قناتك بنجاح!",
        "pay_title": "💳 *تعليمات الدفع*\n\n📢 *القناة:* {channel}\n⏳ *المدة:* {duration}\n💰 *المبلغ:* {price} ETB (أو ~{usd}$ USD)",
        "ad_prompt": "🎉 تم تأكيد الدفع! أرسل نص أو صورة الإعلان.",
        "posted": "🎉 تم نشر الإعلان بنجاح في {channel}!"
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

def get_text(chat_id, key):
    lang = user_lang.get(chat_id, "am")
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
    return "Ethio Ad Multi-Language AI & Global Payments Bot Live!", 200

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

# ቋንቋ መምረጫ
@bot.message_handler(commands=['lang'])
def choose_language(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        InlineKeyboardButton("🇵🇹 Português", callback_data="lang_pt"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")
    )
    bot.reply_to(message, "Please choose your preferred language / ቋንቋ ይምረጡ፦", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_lang_handler(call):
    lang_code = call.data.split('_')[1]
    user_lang[call.message.chat.id] = lang_code
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, get_text(call.message.chat.id, "lang_set"))
    bot.send_message(call.message.chat.id, get_text(call.message.chat.id, "welcome"))

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    if message.chat.id in approved_users:
        del approved_users[message.chat.id]
    bot.reply_to(message, "Process cancelled. / ሂደቱ ተሰርዟል።")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    if message.chat.id not in user_lang:
        choose_language(message)
        return
    bot.reply_to(message, get_text(message.chat.id, "welcome"))

# ቻናል መመዝገብ
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
        bot.reply_to(message, "❌ Invalid number. Please enter numeric digits.")

# ማስታወቂያ መግዛት
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

    bot.reply_to(message, "Select a channel for your ad / ቻናል ይምረጡ፦", reply_markup=markup)

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

    bot.send_message(chat_id, f"Channel: *{ch['channel_name']}*\nSelect ad duration:", reply_markup=markup, parse_mode="Markdown")

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
        f"🇪🇹 *Local Payments (ኢትዮጵያ):*\n"
        f"• Telebirr: `{TELEBIRR_NUM}`\n"
        f"• CBE Bank: `{CBE_ACCOUNT}`\n"
        f"• Abyssinia: `{ABYSSINIA_ACCOUNT}`\n"
        f"• Name: {ACCOUNT_NAME}\n\n"
        f"🌍 *Worldwide Crypto Payments:*\n"
        f"💎 *TON Wallet:*\n`{TON_WALLET}`\n\n"
        f"💵 *USDT (TRC20):*\n`{TRC20_WALLET}`\n\n"
        f"🔹 *USDT / ETH (ERC20):*\n`{ERC20_WALLET}`\n\n"
        f"🌟 *Instant In-App Payments:*\n"
        f"ከታች ያሉትን ቁልፎች በመጠቀም በቀጥታ በ Telegram Stars ወይም በ Card / Google Pay መክፈል ይችላሉ።\n"
        f"⚠️ በባንክ ወይም በክሪፕቶ ከከፈሉ የደረሰኙን ስክሪንሾት እዚህ ይላኩ።"
    )

    markup = InlineKeyboardMarkup()
    star_btn = InlineKeyboardButton(f"🌟 Pay with Telegram Stars ({stars_amount} ⭐️)", callback_data=f"paystars_{call.message.chat.id}")
    card_btn = InlineKeyboardButton(f"💳 Pay with Card / Google Pay (${usd_est})", callback_data=f"paycard_{call.message.chat.id}")
    markup.add(star_btn)
    if PAYMENT_PROVIDER_TOKEN:
        markup.add(card_btn)

    bot.send_message(call.message.chat.id, full_payment_text, reply_markup=markup, parse_mode="Markdown")

# Telegram Stars Invoice
@bot.callback_query_handler(func=lambda call: call.data.startswith('paystars_'))
def handle_star_pay(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    order = user_orders.get(user_id)
    if not order:
        bot.send_message(user_id, "Order details not found. Please try /buy_ad again.")
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

# Card & Google Pay Invoice
@bot.callback_query_handler(func=lambda call: call.data.startswith('paycard_'))
def handle_card_pay(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    order = user_orders.get(user_id)
    if not order:
        bot.send_message(user_id, "Order details not found. Please try /buy_ad again.")
        return

    prices = [LabeledPrice(label=f"Ad on {order['channel_name']}", amount=order['cents'])]
    bot.send_invoice(
        user_id,
        title=f"Ad for {order['channel_name']}",
        description=f"Payment via Card / Google Pay for {order['duration']}",
        invoice_payload=f"card_order_{user_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="USD",
        prices=prices
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Stars ወይም Card/Google Pay ክፍያ ሲፈጸም በራሱ የሚጸድቅበት
@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.chat.id
    order = user_orders.get(user_id)
    if order:
        approved_users[user_id] = order
        bot.reply_to(message, "🎉 Payment received successfully!\n\n" + get_text(user_id, "ad_prompt"))
        bot.send_message(ADMIN_ID, f"🎉 New verified payment received from `{user_id}` for {order['channel_name']}!")

# ፎቶ ሲላክ (ደረሰኝ ወይም ማስታወቂያ)
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
            bot.send_message(ADMIN_ID, f"✅ Ad auto-posted to {target_channel} successfully.")
        except Exception as e:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.reply_to(message, "Ad received! It will be posted by the admin.")
            bot.send_message(ADMIN_ID, f"⚠️ Error auto-posting: {e}")
        return

    if user_id not in user_orders:
        bot.reply_to(message, "Please choose /buy_ad first.")
        return

    order = user_orders[user_id]
    photo_id = message.photo[-1].file_id

    admin_markup = InlineKeyboardMarkup()
    approve_btn = InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}")
    reject_btn = InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")
    admin_markup.add(approve_btn, reject_btn)

    admin_caption = (
        f"📩 *Payment Receipt!*\n\n"
        f"User ID: `{user_id}`\n"
        f"Channel: {order['channel_name']}\n"
        f"Duration: {order['duration']}\n"
        f"Total: {order['final_price']} ETB"
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
        bot.send_message(customer_id, "❌ Payment rejected. Please contact support.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🔴 [REJECTED]")

# የጽሑፍ ማስታወቂያ እና Gemini AI Support
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_or_ai(message):
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

    # Gemini 2.5 Flash AI Assistant
    if ai_client:
        current_l = user_lang.get(user_id, "English/Amharic")
        system_prompt = (
            f"You are the helpful AI assistant for Ethio Telegram Ads platform. "
            f"Respond politely and concisely in the user's language (preferred language: {current_l}). "
            f"Guide users on how to register channels using /register, buy ads with /buy_ad, and pay locally or globally via TON, TRC20, ERC20, Telegram Stars, Google Pay, or Credit Card."
        )
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_prompt}\n\nUser Question: {message.text}"
            )
            bot.reply_to(message, response.text)
            return
        except Exception:
            pass

    bot.reply_to(message, get_text(user_id, "welcome"))

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/webhook")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
