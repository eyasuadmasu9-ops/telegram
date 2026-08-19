import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)

# 1. Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

FULL_NAME, PHONE, AMOUNT, CONFIRM = range(4)

# ------------------- 2. የቦት አሰራር -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    
    welcome_text = (
        f"ሰላም {user_first_name}👋!\n\n"
        "እንኳን ወደ **ኢስት አፍሪካ የቁጠባ እና ብድር ማህበር አነስተኛ ፈጣን ብድር ቦት** በሰላም መጡ።\n\n"
        "ይህ ቦት ከአስቸኳይ የገንዘብ ፍላጎትዎ ጋር ተጣጥሞ ከደመወዝዎ የሚቆረጥ አነስተኛ ብድር በደቂቃዎች ውስጥ እንዲያገኙ ይረዳዎታል።\n\n"
        "ብድር ለመጠየቅ ከታች ያለውን **'🏦 ብድር ይጠይቁ'** የሚለውን ይጫኑ።"
    )
    
    keyboard = [
        [KeyboardButton("🏦 ብድር ይጠይቁ")],
        [KeyboardButton("ℹ️ አሰራር እና የአገልግሎት ክፍያ"), KeyboardButton("📞 እገዛ / ድጋፍ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

# የአሰራር እና የእገዛ መረጃዎች
async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "ℹ️ **የአሰራር መመሪያ እና የአገልግሎት ክፍያ፦**\n\n"
        "1. የብድር ጥያቄዎን በቦቱ በኩል ያቀረባሉ።\n"
        "2. ማህበሩ የደመወዝ መረጃዎን በማረጋገጥ ብድሩን በቴሌብር ይልክልዎታል።\n"
        "3. ክፍያው በወሩ መጨረሻ ከደመወዝዎ ተቆርጦ የሚታሰብ ይሆናል።\n\n"
        "⚙️ **የአገልግሎት ክፍያ፦** 5% ብቻ"
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📞 **እገዛ እና ድጋፍ፦**\n\n"
        "ለማንኛውም ጥያቄ ወይም ተጨማሪ መረጃ የቁጠባ እና ብድር ማህበር ቢሮን ማነጋገር ይችላሉ።\n"
        "📱 ስልክ፦ +251947000012\n"
        "📍 ቢሮ፦ የብድር እና ቁጠባ ማህበር ቢሮ"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# የብድር ጥያቄ ማስጀመሪያ
async def start_loan_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "እባክዎን **ሙሉ ስምዎን** (ከነ አያት) ያስገቡ፦\n"
        "(ምሳሌ፡ አበበ ከበደ ተሰማ)",
        parse_mode='Markdown'
    )
    return FULL_NAME

async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    
    keyboard = [[KeyboardButton("📱 ስልክ ቁጥር አጋራ", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "አመሰግናለሁ! አሁን ከታች ያለውን **'📱 ስልክ ቁጥር አጋራ'** የሚለውን ቁልፍ በመጫን የስልክ ቁጥርዎን ያጋሩ፦",
        reply_markup=reply_markup
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data['phone'] = update.message.contact.phone_number
    else:
        context.user_data['phone'] = update.message.text

    await update.message.reply_text(
        "የሚፈልጉትን የብድር መጠን በብር ያስገቡ፦\n"
        "*(ማሳሰቢያ፦ የመጨረሻው የብድር ወሰን 10,000 ብር ነው)*",
        parse_mode='Markdown'
    )
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        if amount <= 0 or amount > 10000:
            await update.message.reply_text("እባክዎን ከ 500 እስከ 10,000 ብር መካከል ያስገቡ።")
            return AMOUNT
            
        context.user_data['amount'] = amount
        
        service_fee = amount * 0.05
        total_deduction = amount + service_fee
        
        context.user_data['service_fee'] = service_fee
        context.user_data['total_deduction'] = total_deduction
        
        summary_text = (
            "📋 **የብድር ጥያቄ ማጠቃለያ፦**\n\n"
            f"👤 **ተበዳሪ:** {context.user_data['full_name']}\n"
            f"📞 **ስልክ:** {context.user_data['phone']}\n"
            f"💵 **የተጠየቀው ብድር:** {amount:,.2f} ብር\n"
            f"⚙️ **የአገልግሎት ክፍያ (5%):** {service_fee:,.2f} ብር\n"
            f"───────────────────────\n"
            f"📌 **በወሩ መጨረሻ ከደመወዝ የሚቆረጥ:** {total_deduction:,.2f} ብር\n\n"
            "መረጃው ትክክል ከሆነ **'✅ አረጋግጥ'** የሚለውን ይጫኑ።"
        )
        
        keyboard = [["✅ አረጋግጥ", "❌ ሰርዝ"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(summary_text, parse_mode='Markdown', reply_markup=reply_markup)
        return CONFIRM

    except ValueError:
        await update.message.reply_text("እባክዎን የብድሩን መጠን በቁጥር ብቻ ያስገቡ (ምሳሌ፦ 3000)።")
        return AMOUNT

async def confirm_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    
    if user_choice == "✅ አረጋግጥ":
        keyboard = [
            [KeyboardButton("🏦 ብድር ይጠይቁ")],
            [KeyboardButton("ℹ️ አሰራር እና የአገልግሎት ክፍያ"), KeyboardButton("📞 እገዛ / ድጋፍ")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        success_text = (
            "🎉 **የብድር ጥያቄዎ በተሳካ ሁኔታ ተልኳል!**\n\n"
            "የማህበሩ አመራሮች ጥያቄዎን መዝግበው የደመወዝ መረጃዎን በማረጋገጥ በ አጭር ጊዜ ውስጥ በቴሌብር (Telebirr) ገቢ ያደርጉልዎታል።\n\n"
            "ስለመረጡን እናመሰግናለን!"
        )
        await update.message.reply_text(success_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text("የብድር ጥያቄው ተሰርዟል።", reply_markup=ReplyKeyboardMarkup([["🏦 ብድር ይጠይቁ"]], resize_keyboard=True))
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("የተጀመረው ሂደት ተቋርጧል።")
    return ConversationHandler.END

# ------------------- 3. ዋና የማስፈጸሚያ -------------------

if __name__ == '__main__':
    BOT_TOKEN = "8673031847:AAEH0PwU7dCggs9jXc9yJ_wvP9p6HqgnoYc"
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    loan_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('.*ብድር ይጠይቁ.*'), start_loan_process)],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_loan)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('.*አሰራር.*'), info_handler))
    app.add_handler(MessageHandler(filters.Regex('.*እገዛ.*'), help_handler))
    app.add_handler(loan_conv_handler)

    print("🤖 የቁጠባ እና ብድር ቦቱ ስራ ጀምሯል...")
    app.run_polling()
