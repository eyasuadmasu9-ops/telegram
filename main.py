import os
import csv
import urllib.request
import telebot
from flask import Flask

# 1. ቶከንና ቦት ማዘጋጀት
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 2. የ Google Sheet CSV ሊንክ
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1jvaeMiflCKBpSJciUotKf_i9fne_PzZ1w4BPjAChQZc/export?format=csv"

# 3. Render እንዳይተኛ የሚያደርገው Flask Web Server
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online!"

# 4. ከ Google Sheet ላይ የአባላትን መረጃ የማንበቢያ ተግባር
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

# 5. የቴሌግራም ቦቱ መልዕክት ሲላክለት የሚሰጠው ምላሽ
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "እንኳን ደህና መጡ! እባክዎን የ SAP ID ቁጥርዎን ያስገቡ፦")

@bot.message_handler(func=lambda message: True)
def check_sap(message):
    user_input = message.text.strip()
    members_data = get_sheet_data()
    
    if user_input in members_data:
        member = members_data[user_input]
        bot.reply_to(
            message, 
            f"✅ የ SAP ID ተረጋግጧል!\n\n"
            f"👤 ስም፦ {member['name']}\n"
            f"📞 ስልክ፦ {member['phone']}\n"
            f"🆔 SAP ID፦ {user_input}"
        )
    else:
        bot.reply_to(message, "❌ ይቅርታ፣ ይህ የ SAP ID ቁጥር በቋታችን/በመዝገባችን ላይ አልተገኘም። እባክዎን ቁጥሩን አስተካክለው እንደገና ይሞክሩ።")

if __name__ == "__main__":
    import threading
    
    # ቦቱን በተለየ Thread ማስኬድ
    def run_bot():
        bot.infinity_polling()

    threading.Thread(target=run_bot).start()
    
    # Flask Server ማስኬድ (Render ላይ Port 8080 ወይም Render የሰጠውን ይጠቀማል)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
