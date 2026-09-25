import os
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

# የሀገር ውስጥ ክፍያ መረጃ
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

LANG_STRINGS = {
    "am": {
        "welcome": "እንኳን ደህና መጡ! 📢\n\n• ቻናል ለመመዝገብ፦ /register\n• ማስታወቂያ ለመግዛት፦ /buy_ad\n• ቋንቋ ለመቀየር፦ /lang\n• አሰራር ለመሰረዝ፦ /cancel\n• AI ለማናገር፦ /ask ወይም በቀጥታ ጽፈው ይላኩ።",
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
        "welcome": "Welcome! 📢\n\n• Register channel: /register\n• Buy ad: /buy_ad\n• Change language: /lang\n• Cancel operation: /cancel\n• Chat with AI: /ask or just type your question.",
        "lang_set": "Language switched to English.",
        "enter_ch_name": "Please enter your channel name:",
        "enter_ch_link": "Please enter channel link (e.g. https://t.me/wodtech1):",
        "enter_price": "Enter starting price in ETB (e.g. 1000):",
        "registered": "✅ Your channel has been registered successfully!",
        "pay_title": "💳 *Payment Instructions*\n\n📢 *Channel:* {channel}\n⏳ *Duration:* {duration}\n💰 *Total:* {price} ETB (or ~{usd}$ USD)",
        "ad_prompt": "🎉 Payment approved! Please send the ad text or photo to be published.",
        "posted": "🎉 Your ad has been published to {channel} successfully!"
    },
    "ar": {
        "welcome": "أهلاً بك! 📢\n\n• تسجيل قناة: /register\n• شراء إعلان: /buy_ad\n• تغيير اللغة: /lang\n• إلغاء: /cancel\n• المساعد الذكي: /ask أو أرسل سؤالك مباشرة.",
        "lang_set": "تم تغيير اللغة إلى العربية.",
        "enter_ch_name": "يرجى إدخال اسم القناة:",
        "enter_ch_link": "يرجى إدخال رابط القناة:",
        "enter_price": "أدخل السعر الأساسي بالـ ETB:",
        "registered": "✅ تم تسجيل قناتك بنجاح!",
        "pay_title": "💳 *تعليمات الدفع*\n\n📢 *القناة:* {channel}\n⏳ *المدة:* {duration}\n💰 *المبلغ:* {price} ETB (أو ~{usd}$ USD)",
        "ad_prompt": "🎉 تم تأكيد الدفع! أرسل نص أو صورة الإعلان.",
        "posted": "🎉 تم نشر الإعلان بنجاح في {channel}!"
    },
    "fr": {
        "welcome": "Bienvenue! 📢\n\n• Enregistrer: /register\n• Acheter pub: /buy_ad\n• Langue: /lang\n• Annuler: /cancel\n• Parler avec IA: /ask ou écrivez votre message.",
        "lang_set": "Langue changée en Français.",
        "enter_ch_name": "Entrez le nom de votre chaîne:",
        "enter_ch_link": "Entrez le lien de la chaîne:",
        "enter_price": "Entrez le prix de base en ETB:",
        "registered": "✅ Votre chaîne est enregistrée avec succès!",
        "pay_title": "💳 *Instructions de paiement*\n\n📢 *Chaîne:* {channel}\n⏳ *Durée:* {duration}\n💰 *Total:* {price} ETB (ou ~{usd}$ USD)",
        "ad_prompt": "🎉 Paiement approuvé! Envoyez votre texte publicitaire ou photo.",
        "posted": "🎉 Publicité publiée sur {channel} avec succès!"
    },
    "es": {
        "welcome": "¡Bienvenido! 📢\n\n• Registrar canal: /register\n• Comprar anuncio: /buy_ad\n• Cambiar idioma: /lang\n• Cancelar: /cancel\n• Hablar con IA: /ask o envíe su mensaje.",
        "lang_set": "Idioma cambiado a Español.",
        "enter_ch_name": "Ingrese el nombre del canal:",
        "enter_ch_link": "Ingrese el enlace del canal:",
        "enter_price": "Ingrese el precio base en ETB:",
        "registered": "✅ ¡Canal registrado con éxito!",
        "pay_title": "💳 *Instrucciones de pago*\n\n📢 *Canal:* {channel}\n⏳ *Duración:* {duration}\n💰 *Total:* {price} ETB (o ~{usd}$ USD)",
        "ad_prompt": "🎉 ¡Pago aprobado! Envíe el texto o la imagen de su anuncio.",
        "posted": "🎉 ¡Anuncio publicado en {channel} con éxito!"
    },
    "ru": {
        "welcome": "Добро пожаловать! 📢\n\n• Добавить канал: /register\n• Купить рекламу: /buy_ad\n• Язык: /lang\n• Отмена: /cancel\n• Чат с ИИ: /ask или просто задайте вопрос.",
        "lang_set": "Язык изменен на Русский.",
        "enter_ch_name": "Введите название канала:",
        "enter_ch_link": "Введите ссылку на канал:",
        "enter_price": "Введите базовую цену в ETB:",
        "registered": "✅ Канал успешно добавлен!",
        "pay_title": "💳 *Оплата рекламы*\n\n📢 *Канал:* {channel}\n⏳ *Срок:* {duration}\n💰 *Сумма:* {price} ETB (или ~{usd}$ USD)",
        "ad_prompt": "🎉 Оплата подтверждена! Отправьте текст или фото рекламы.",
        "posted": "🎉 Реклама успешно опубликована в {channel}!"
    },
    "pt": {
        "welcome": "Bem-vindo! 📢\n\n• Registrar canal: /register\n• Comprar anúncio: /buy_ad\n• Mudar idioma: /lang\n• Cancelar: /cancel\n• Falar com IA: /ask ou envie mensagem.",
        "lang_set": "Idioma alterado para Português.",
        "enter_ch_name": "Digite o nome do canal:",
        "enter_ch_link": "Digite o link do canal:",
        "enter_price": "Digite o preço base em ETB:",
        "registered": "✅ Canal registrado com sucesso!",
        "pay_title": "💳 *Instruções de pagamento*\n\n📢 *Canal:* {channel}\n⏳ *Duração:* {duration}\n💰 *Total:* {price} ETB (ou ~{usd}$ USD)",
        "ad_prompt": "🎉 Pagamento aprovado! Envie o texto ou a foto do anúncio.",
        "posted": "🎉 Anúncio publicado em {channel} com sucesso!"
    },
    "zh": {
        "welcome": "欢迎！📢\n\n• 注册频道：/register\n• 购买广告：/buy_ad\n• 更改语言：/lang\n• 取消操作：/cancel\n• AI 对话：/ask 或直接输入问题。",
        "lang_set": "语言已切换为中文。",
        "enter_ch_name": "请输入您的频道名称：",
        "enter_ch_link": "请输入频道链接：",
        "enter_price": "请输入基础价格 (ETB)：",
        "registered": "✅ 您的频道已成功注册！",
        "pay_title": "💳 *支付指南*\n\n📢 *频道：* {channel}\n⏳ *时长：* {duration}\n💰 *总价：* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 支付成功！请发送要在频道中发布的广告内容（文字或图片）。",
        "posted": "🎉 您的广告已成功发布到 {channel}！"
    },
    "hi": {
        "welcome": "नमस्ते! 📢\n\n• चैनल पंजीकृत करें: /register\n• विज्ञापन खरीदें: /buy_ad\n• भाषा बदलें: /lang\n• रद्द करें: /cancel\n• AI से पूछें: /ask या अपना प्रश्न टाइप करें।",
        "lang_set": "भाषा हिंदी में बदल दी गई है।",
        "enter_ch_name": "कृपया अपने चैनल का नाम दर्ज करें:",
        "enter_ch_link": "चैनल का लिंक दर्ज करें:",
        "enter_price": "शुरुआती मूल्य (ETB में) दर्ज करें:",
        "registered": "✅ आपका चैनल सफलतापूर्वक पंजीकृत हो गया है!",
        "pay_title": "💳 *भुगतान निर्देश*\n\n📢 *चैनल:* {channel}\n⏳ *अवधि:* {duration}\n💰 *कुल राशि:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 भुगतान स्वीकृत! कृपया प्रकाशित करने के लिए अपना विज्ञापन भेजें।",
        "posted": "🎉 आपका विज्ञापन {channel} पर सफलतापूर्वक प्रकाशित हुआ!"
    },
    "de": {
        "welcome": "Willkommen! 📢\n\n• Kanal registrieren: /register\n• Werbung kaufen: /buy_ad\n• Sprache ändern: /lang\n• Abbrechen: /cancel\n• Mit KI chatten: /ask oder Frage eingeben.",
        "lang_set": "Sprache auf Deutsch umgestellt.",
        "enter_ch_name": "Geben Sie Ihren Kanalnamen ein:",
        "enter_ch_link": "Geben Sie den Kanallink ein:",
        "enter_price": "Grundpreis in ETB eingeben:",
        "registered": "✅ Ihr Kanal wurde erfolgreich registriert!",
        "pay_title": "💳 *Zahlungsanweisungen*\n\n📢 *Kanal:* {channel}\n⏳ *Dauer:* {duration}\n💰 *Gesamt:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 Zahlung bestätigt! Senden Sie Ihren Anzeigentext oder Ihr Foto.",
        "posted": "🎉 Ihre Anzeige wurde erfolgreich auf {channel} veröffentlicht!"
    },
    "tr": {
        "welcome": "Hoş geldiniz! 📢\n\n• Kanal ekle: /register\n• Reklam al: /buy_ad\n• Dil değiştir: /lang\n• İptal: /cancel\n• Yapay Zeka ile konuş: /ask veya sorunuzu yazın.",
        "lang_set": "Dil Türkçe olarak ayarlandı.",
        "enter_ch_name": "Lütfen kanal adınızı girin:",
        "enter_ch_link": "Kanal bağlantısını girin:",
        "enter_price": "ETB cinsinden taban fiyatı girin:",
        "registered": "✅ Kanalınız başarıyla kaydedildi!",
        "pay_title": "💳 *Ödeme Talimatı*\n\n📢 *Kanal:* {channel}\n⏳ *Süre:* {duration}\n💰 *Tutar:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 Ödeme onaylandı! Lütfen yayınlanacak reklamı gönderin.",
        "posted": "🎉 Reklamınız {channel} kanalında başarıyla yayınlandı!"
    },
    "it": {
        "welcome": "Benvenuto! 📢\n\n• Registra canale: /register\n• Acquista pubblicità: /buy_ad\n• Cambia lingua: /lang\n• Annulla: /cancel\n• Parla con IA: /ask o scrivi la tua domanda.",
        "lang_set": "Lingua impostata su Italiano.",
        "enter_ch_name": "Inserisci il nome del tuo canale:",
        "enter_ch_link": "Inserisci il link del canale:",
        "enter_price": "Inserisci il prezzo base in ETB:",
        "registered": "✅ Il tuo canale è stato registrato!",
        "pay_title": "💳 *Istruzioni di pagamento*\n\n📢 *Canale:* {channel}\n⏳ *Durata:* {duration}\n💰 *Totale:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 Pagamento approvato! Invia il testo o la foto dell'annuncio.",
        "posted": "🎉 Annuncio pubblicato con successo su {channel}!"
    },
    "ja": {
        "welcome": "ようこそ！📢\n\n• チャンネル登録：/register\n• 広告購入：/buy_ad\n• 言語変更：/lang\n• キャンセル：/cancel\n• AIに質問：/ask または直接質問を入力。",
        "lang_set": "言語が日本語に設定されました。",
        "enter_ch_name": "チャンネル名を入力してください：",
        "enter_ch_link": "チャンネルリンクを入力してください：",
        "enter_price": "基本料金（ETB）を入力してください：",
        "registered": "✅ チャンネルが登録されました！",
        "pay_title": "💳 *お支払い手順*\n\n📢 *チャンネル：* {channel}\n⏳ *期間：* {duration}\n💰 *合計：* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 お支払いが確認されました！掲載する広告内容を送信してください。",
        "posted": "🎉 広告が {channel} に正常に投稿されました！"
    },
    "ko": {
        "welcome": "환영합니다! 📢\n\n• 채널 등록: /register\n• 광고 구매: /buy_ad\n• 언어 변경: /lang\n• 취소: /cancel\n• AI 대화: /ask 또는 질문을 직접 입력하세요.",
        "lang_set": "언어가 한국어로 변경되었습니다.",
        "enter_ch_name": "채널 이름을 입력하세요:",
        "enter_ch_link": "채널 링크를 입력하세요:",
        "enter_price": "기본 가격(ETB)을 입력하세요:",
        "registered": "✅ 채널이 성공적으로 등록되었습니다!",
        "pay_title": "💳 *결제 안내*\n\n📢 *채널:* {channel}\n⏳ *기간:* {duration}\n💰 *금액:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 결제가 승인되었습니다! 게재할 광고(텍스트 또는 사진)를 보내주세요.",
        "posted": "🎉 광고가 {channel} 채널에 게시되었습니다!"
    },
    "sw": {
        "welcome": "Karibu! 📢\n\n• Sajili idhaa: /register\n• Nunua tangazo: /buy_ad\n• Badilisha lugha: /lang\n• Ghairi: /cancel\n• Ongea na AI: /ask au andika swali lako.",
        "lang_set": "Lugha imebadilishwa kuwa Kiswahili.",
        "enter_ch_name": "Tafadhali weka jina la idhaa yako:",
        "enter_ch_link": "Weka kiungo cha idhaa:",
        "enter_price": "Weka bei ya kuanzia kwa ETB:",
        "registered": "✅ Idhaa yako imesajiliwa kikamilifu!",
        "pay_title": "💳 *Maagizo ya Malipo*\n\n📢 *Idhaa:* {channel}\n⏳ *Muda:* {duration}\n💰 *Jumla:* {price} ETB (~{usd}$ USD)",
        "ad_prompt": "🎉 Malipo yamethibitishwa! Tuma tangazo lako sasa.",
        "posted": "🎉 Tangazo lako limechapishwa kwenye {channel}!"
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/channels', methods=['GET'])
def get_channels():
    conn = get_db_connection()
    channels = conn.execute('SELECT * FROM channels').fetchall()
    conn.close()
    return jsonify([dict(row) for row in channels])

# አስተማማኝ AI ሞዴሎችን የሚጠቀም ተግባር (503 እንዳይመጣ)
def call_gemini_models(system_prompt, question_text):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return "API Key not configured."

    ai_client = genai.Client(api_key=key.strip())
    # 503 እንዳያጋጥም ቅድሚያ የሚሰጣቸው የተረጋጉ ሞዴሎች
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']

    for m in models_to_try:
        try:
            res = ai_client.models.generate_content(
                model=m,
                contents=f"{system_prompt}\n\nUser Question: {question_text}"
            )
            if res and res.text:
                return res.text
        except Exception as e:
            continue
    return "ይቅርታ፣ የ AI ሰርቨር ተጨናንቋል። እባክዎ ከጥቂት ሰከንዶች በኋላ ይሞክሩ።"

# የድረ-ገጹ AI API
@app.route('/api/ask_ai', methods=['POST'])
def api_ask_ai():
    data = request.get_json() or {}
    query = data.get('query', '')
    lang = data.get('lang', 'am')

    system_prompt = (
        f"You are the official smart AI assistant for Ethio Telegram Ads catalog. "
        f"Always respond fluently and concisely in this language code: {lang}. "
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

# 15 ቋንቋዎች መምረጫ
@bot.message_handler(commands=['lang'])
def choose_language(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
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

# የቴሌግራም ቦት AI ምላሽ
def generate_ai_response(user_id, question_text):
    current_l = user_lang.get(user_id, "am")
    system_prompt = (
        f"You are the official smart AI assistant for 'Ethio Telegram Ads' platform. "
        f"Respond politely and concisely in the user's selected language: {current_l}. "
        f"Provide short, helpful answers. Commands: /register to add a channel, /buy_ad to purchase ads, "
        f"/lang to switch language, /cancel to reset. "
        f"Payments: Telebirr, CBE, Abyssinia, Telegram Stars, and Crypto (TON, TRC20, ERC20)."
    )
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
    bot.reply_to(message, "Process cancelled. / ሂደቱ ተሰርዟል።")

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
        bot.reply_to(message, "❌ Invalid number. Please enter digits only.")

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

    bot.reply_to(message, "Select a channel / ቻናል ይምረጡ፦", reply_markup=markup)

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
        f"🇪🇹 *Local Payments (ኢትዮጵያ):*\n"
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

# Telegram Stars Invoice
@bot.callback_query_handler(func=lambda call: call.data.startswith('paystars_'))
def handle_star_pay(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    order = user_orders.get(user_id)
    if not order:
        bot.send_message(user_id, "Order not found. Try /buy_ad.")
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

# Card Invoice
@bot.callback_query_handler(func=lambda call: call.data.startswith('paycard_'))
def handle_card_pay(call):
    bot.answer_callback_query(call.id)
    user_id = call.message.chat.id
    order = user_orders.get(user_id)
    if not order:
        bot.send_message(user_id, "Order not found.")
        return

    prices = [LabeledPrice(label=f"Ad on {order['channel_name']}", amount=order['cents'])]
    bot.send_invoice(
        user_id,
        title=f"Ad for {order['channel_name']}",
        description=f"Payment for {order['duration']}",
        invoice_payload=f"card_order_{user_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="USD",
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
        bot.send_message(customer_id, "❌ Payment rejected. Contact admin.")
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
