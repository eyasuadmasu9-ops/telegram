import os
import csv
import urllib.request
import telebot
from telebot import types
from flask import Flask
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1jvaeMiflCKBpSJciUotKf_i9fne_PzZ1w4BPjAChQZc/export?format=csv"
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID')

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online!"

user_data = {}

def get_sheet_data():
    members = {}
    try:
        req = urllib.request.Request(
            SHEET_CSV_URL, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            lines = [line.decode('utf-8') for line in response.readlines()]
            reader = csv.DictReader(lines)
            for row in reader:
                sap_id = row.get('Sap Id', '').strip()
                phone = row.get('Phone Number', '').strip()
                name = row.get('Full Name', '').strip()
                if sap_id:
                    members[sap_id] = {'name': name, 'phone': phone}
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
    return members

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton(text="📱 የስልክ ቁጥርዎን ያጋሩ", request_contact=True)
    markup.add(button)
    
    bot.send_message(
        chat_id, 
        f"ሰላም {message.from_user.first_name}!\nእንኳን ወደ ኢስት አፍሪካ የገንዘብ ቁጠባ እና ብድር ህብረት ስራ ማህበር የዲጂታል ብድር አገልግሎት በሰላም መጡ።\n\nየብድር ሂደቱን ለመጀመር እባክዎን ከታች ያለውን ቁልፍ ተጭነው የስልክ ቁጥርዎን ያጋሩ፡", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    phone_number = message.contact.phone_number
    user_data[chat_id]['phone'] = phone_number
    
    msg = bot.send_message(
        chat_id, 
        "✅ የስልክ ቁጥርዎ ተቀብለናል!\n\nእባክዎን የ **SAP ID** ቁጥርዎን ያስገቡ፡",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_sap_step)

def process_sap_step(message):
    chat_id = message.chat.id
    sap_id = message.text.strip()
    
    members_data = get_sheet_data()
    
    if sap_id in members_data:
        member = members_data[sap_id]
        user_data[chat_id]['sap_id'] = sap_id
        user_data[chat_id]['name'] = member['name']
        
        msg = bot.send_message(
            chat_id,
            f"✅ የአባልነት ሁኔታዎ ተረጋግጧል!\n👤 ስም፦ {member['name']}\n\nለመበደር የሚፈልጉትን የገንዘብ መጠን በቁጥር ያስገቡ (ለምሳሌ፦ 10000)፦"
        )
        bot.register_next_step_handler(msg, process_amount_step)
    else:
        msg = bot.send_message(
            chat_id,
            "❌ ይቅርታ፣ ይህ የ SAP ID ቁጥር በመዝገባችን ላይ አልተገኘም። እባክዎን ትክክለኛውን የ SAP ID እንደገና ያስገቡ፦"
        )
        bot.register_next_step_handler(msg, process_sap_step)

def process_amount_step(message):
    chat_id = message.chat.id
    amount = message.text.strip()
    user_data[chat_id]['amount'] = amount
    
    msg = bot.send_message(
        chat_id,
        f"💵 የተጠየቀው ብድር፦ {amount} ETB\nመመላሻ ቀን መቼ እንደሆነ ይጻፉ (ለምሳሌ፦ 25/12/2018 ወይም የደሞዝ ቀን)፦"
    )
    bot.register_next_step_handler(msg, process_date_step)

def process_date_step(message):
    chat_id = message.chat.id
    return_date = message.text.strip()
    user_data[chat_id]['return_date'] = return_date
    
    data = user_data[chat_id]
    try:
        amt = float(data['amount'])
        fee = amt * 0.15
        total = amt + fee
    except:
        fee, total = 0, 0

    summary = (
        f"📋 **የብድር ጥያቄ ማጠቃለያ**\n\n"
        f"👤 ስም፦ {data.get('name', 'N/A')}\n"
        f"🆔 SAP ID፦ {data.get('sap_id', 'N/A')}\n"
        f"📱 ስልክ፦ {data.get('phone', 'N/A')}\n"
        f"💰 የብድር መጠን፦ {amt:,.2f} ETB\n"
        f"🏷 የአገልግሎት ክፍያ (15%)፦ {fee:,.2f} ETB\n"
        f"🔴 ጠቅላላ የሚመለስ መጠን፦ {total:,.2f} ETB\n"
        f"📅 የመመላሻ ቀን፦ {return_date}\n\n"
        f"መረጃው ትክክል ከሆነ '✅ አረጋግጣለሁ' የሚለውን ቁልፍ ይጫኑ።"
    )
    
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("✅ አረጋግጣለሁ"))
    
    msg = bot.send_message(chat_id, summary, parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(msg, confirm_loan_step)

def confirm_loan_step(message):
    chat_id = message.chat.id
    data = user_data.get(chat_id, {})
    
    # ለተበዳሪው ማረጋገጫ መላክ
    bot.send_message(
        chat_id, 
        "🎉 የብድር ጥያቄዎ በተሳካ ሁኔታ ለአመራሮች ተልኳል!\n\nየማህበሩ አመራሮች ጥያቄዎትን ተመልክተው በቴሌብር (Telebirr) ገቢ ያደርጉልዎታል። አመሰግናለሁ!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # ለግሩፕ ማሳወቂያ መላክ
    if GROUP_CHAT_ID:
        try:
            amt = float(data.get('amount', 0))
            fee = amt * 0.15
            total = amt + fee
        except:
            total = 0

        group_msg = (
            f"🚨 **አዲስ የብድር ጥያቄ ቀርቧል!**\n\n"
            f"🏛 ማህበር፦ ኢስት አፍሪካ የገንዘብ ቁጠባ እና ብድር ህብረት ስራ ማህበር\n"
            f"👤 ተበዳሪ፦ {data.get('name')}\n"
            f"🆔 SAP ID፦ {data.get('sap_id')}\n"
            f"📱 ስልክ (Telebirr)፦ {data.get('phone')}\n"
            f"💵 የተጠየቀው ብድር፦ {data.get('amount')} ETB\n"
            f"📈 ከደሞዝ የሚቆረጠው፦ {total:,.2f} ETB\n"
            f"📅 የመመላሻ ቀን፦ {data.get('return_date')}\n\n"
            f"📌 እባክዎን መረጃውን አረጋግጣችሁ በቴሌብር ክፍያውን ፈፅሙ።"
        )
        bot.send_message(GROUP_CHAT_ID, group_msg, parse_mode="Markdown")

 if __name__ == "__main__":
    def run_bot():
        # Clear any pending updates or conflicting connections
        bot.remove_webhook()
        bot.infinity_polling(skip_pending=True)

    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

