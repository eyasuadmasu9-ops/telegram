import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# -------------------------------------------------------------
# 1. FLASK SERVER (Render እንዳይዘጋ የሚያደርግ)
# -------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "East Africa SACCO Bot is Running Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# -------------------------------------------------------------
# 2. CONFIGURATION (እዚህ ጋር የራስህን መረጃዎች አስገባ)
# -------------------------------------------------------------
BOT_TOKEN = "8673031847:AAEH0PwU7dCggs9jXc9yJ_wvP9p6HqgnoYc"  # የቦትህን ቶከን አስገባ
BOARD_GROUP_ID = "-1003507773519"     # የአመራሮቹ የቴሌግራም ግሩፕ Chat ID

# የተፈቀዱ የማህበሩ አባላት የስልክ ቁጥር ዝርዝር (ምሳሌ)
REGISTERED_MEMBERS = [
    "0923789788",
    "0991738348",
    "0929135294"
]

# States
PHONE, AMOUNT, REPAY_DATE, CONFIRM = range(4)

# -------------------------------------------------------------
# 3. BOT HANDLERS
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # የስልክ ቁጥር መጠየቂያ ቁልፍ
    keyboard = [[KeyboardButton(text="📱 የስልክ ቁጥርዎን ያጋሩ", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"ሰላም {user_name}!\n"
        f"እንኳን ወደ **ኢስት አፍሪካ የገንዘብ ቁጠባ እና ብድር ህብረት ስራ ማህበር** የዲጂታል ብድር አገልግሎት በሰላም መጡ።\n\n"
        f"የብድር ሂደቱን ለመጀመር እባክዎን ከታች ያለውን ቁልፍ ተጭነው የስልክ ቁጥርዎን ያጋሩ፡",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact:
        phone_number = contact.phone_number.replace("+251", "0").replace("251", "0")
    else:
        phone_number = update.message.text.strip()

    context.user_data['phone'] = phone_number

    # የአባልነት ማረጋገጫ (Member Check)
    # ማስታወሻ፦ ለሙከራ እንዲመችህ ሁሉንም ማሳለፍ ከፈለግክ ከታች ያለውን 'if' ማስተካከል ትችላለህ
    if phone_number not in REGISTERED_MEMBERS:
         await update.message.reply_text(
             f"⚠️ ይቅርታ፣ የስልክ ቁጥርዎ ({phone_number}) በኢስት አፍሪካ ማህበር አባላት መዝገብ ውስጥ አልተገኘም።\n"
             f"እባክዎን ለማህበሩ አበልፃጊ ወይም አመራሮች ያመልክቱ።",
             reply_markup=ReplyKeyboardRemove()
         )
         return ConversationHandler.END

    await update.message.reply_text(
        "✅ የአባልነትዎ ሁኔታ ተረጋግጧል!\n\n"
        "ለመበደር የሚፈልጉትን የገንዘብ መጠን በቁጥር ያስገቡ (ለምሳሌ፦ 10000)፡",
        reply_markup=ReplyKeyboardRemove()
    )
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("እባክዎን ትክክለኛ የገንዘብ መጠን በቁጥር ብቻ ያስገቡ (ለምሳሌ፦ 10000)፡")
        return AMOUNT

    amount = int(text)
    context.user_data['amount'] = amount
    
    # የ 15% አገልግሎት ክፍያ ስሌት
    service_fee = amount * 0.15
    total_repayment = amount + service_fee

    context.user_data['service_fee'] = service_fee
    context.user_data['total_repayment'] = total_repayment

    await update.message.reply_text(
        f"💵 **የተጠየቀው ብድር፦** {amount:,.2f} ብር\n"
        f"መመለሻ ቀኑ መቼ እንደሆነ ይጻፉ (ለምሳሌ፦ 25/12/2018 ወይም የደመወዝ ቀን)፡",
        parse_mode="Markdown"
    )
    return REPAY_DATE

async def get_repay_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repay_date = update.message.text
    context.user_data['repay_date'] = repay_date

    amount = context.user_data['amount']
    service_fee = context.user_data['service_fee']
    total_repayment = context.user_data['total_repayment']
    phone = context.user_data['phone']
    user = update.effective_user.full_name

    summary = (
        f"📋 **የብድር ጥያቄ ማጠቃለያ**\n\n"
        f"👤 **ስም፦** {user}\n"
        f"📱 **ስልክ፦** {phone}\n"
        f"💰 **የብድር መጠን፦** {amount:,.2f} ETB\n"
        f"🏷️ **የአገልግሎት ክፍያ (15%)፦** {service_fee:,.2f} ETB\n"
        f"🔴 **ጠቅላላ የሚመለስ መጠን፦** {total_repayment:,.2f} ETB\n"
        f"📅 **የመመለሻ ቀን፦** {repay_date}\n\n"
        f"መረጃው ትክክል ከሆነ **'✅ አረጋግጥ'** የሚለውን ቁልፍ ይጫኑ።"
    )

    keyboard = [["✅ አረጋግጥ", "❌ ሰርዝ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode="Markdown")
    return CONFIRM

async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = update.message.text

    if response == "✅ አረጋግጥ":
        user = update.effective_user.full_name
        phone = context.user_data['phone']
        amount = context.user_data['amount']
        total = context.user_data['total_repayment']
        repay_date = context.user_data['repay_date']

        # 1. ለሰራተኛው የማረጋገጫ መልእክት
        await update.message.reply_text(
            "🎉 **የብድር ጥያቄዎ በተሳካ ሁኔታ ለአመራሮች ተልኳል!**\n\n"
            "የማህበሩ አመራሮች ጥያቄዎትን ተመልክተው በቴሌብር (Telebirr) ገቢ ያደርጉልዎታል። አመሰግናለሁ!",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )

        # 2. ለአመራሮቹ የቴሌግራም ግሩፕ ጥያቄውን መላክ
        board_notification = (
            f"🚨 **አዲስ የብድር ጥያቄ ቀርቧል!**\n\n"
            f"🏛️ **ማህበር፦** ኢስት አፍሪካ የገንዘብ ቁጠባ እና ብድር ህብረት ስራ ማህበር\n"
            f"👤 **ተበዳሪ፦** {user}\n"
            f"📱 **ስልክ (Telebirr)፦** {phone}\n"
            f"💵 **የተጠየቀው ብድር፦** {amount:,.2f} ETB\n"
            f"📈 **ከደመወዝ የሚቆረጥ፦** {total:,.2f} ETB\n"
            f"📅 **የመመለሻ ቀን፦** {repay_date}\n\n"
            f"📌 *እባክዎን መረጃውን አረጋግጠው በቴሌብር ክፍያውን ይፈጽሙ።*"
        )
        
        try:
            await context.bot.send_message(
                chat_id=BOARD_GROUP_ID,
                text=board_notification,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error sending to group: {e}")

    else:
        await update.message.reply_text(
            "❌ የብድር ጥያቄው ተሰርዟል። እንደገና ለመጀመር /start ብለው ይፃፉ።",
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሂደቱ ተቋርጧል።", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# -------------------------------------------------------------
# 4. MAIN FUNCTION
# -------------------------------------------------------------
def main():
    # Flask ን በድብቅ (Background thread) ማስነሳት
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Telegram Bot ን ማስነሳት
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, get_phone)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            REPAY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_repay_date)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
