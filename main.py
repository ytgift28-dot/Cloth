import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from gradio_client import Client, handle_file

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = "8629018568:AAEZyaeP63ETmYThyUJvko7GcHX8ZOBpW-U"
ADMIN_ID = 6941003064  # আপনার আইডি
CHANNEL_USERNAME = "@SH_tricks"
ADS_MONETAG = "https://omg10.com/4/10644374"
ADS_ADSTERRA = "https://www.effectivegatecpm.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

user_credits = {} 
USER_PHOTO, CLOTH_PHOTO = range(2)

# --- Render Port Binding ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running with Admin Panel!")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- অ্যাডমিন ফাংশনস ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = (f"👤 **অ্যাডমিন প্যানেল**\n\n"
           f"মোট ইউজার: {len(user_credits)}\n"
           f"কমান্ডসমূহ:\n"
           f"/add [user_id] [amount] - ক্রেডিট দিতে\n"
           f"/broadcast [message] - সবাইকে মেসেজ দিতে")
    await update.message.reply_text(msg, parse_mode='Markdown')

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0])
        amt = int(context.args[1])
        user_credits[uid] = user_credits.get(uid, 0) + amt
        await update.message.reply_text(f"✅ ইউজার {uid} কে {amt} ক্রেডিট দেওয়া হয়েছে।")
    except: await update.message.reply_text("ব্যবহার: /add [user_id] [amount]")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    if not text: return
    count = 0
    for uid in user_credits.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **নোটিশ:**\n\n{text}", parse_mode='Markdown')
            count += 1
        except: continue
    await update.message.reply_text(f"✅ {count} জন ইউজারকে মেসেজ পাঠানো হয়েছে।")

# --- মূল বটের লজিক ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_credits: user_credits[user_id] = 5
    kb = [['👕 Start Dressing'], ['💰 Get Credit', '📊 Balance']]
    if user_id == ADMIN_ID: kb.append(['⚙️ Admin Panel'])
    await update.message.reply_text(f"স্বাগতম! ব্যালেন্স: {user_credits[user_id]}", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def start_dressing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_credits.get(update.effective_user.id, 0) < 1:
        await update.message.reply_text("ক্রেডিট নেই!")
        return ConversationHandler.END
    await update.message.reply_text("নিজের একটি ছবি পাঠান।")
    return USER_PHOTO

async def get_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = await update.message.photo[-1].get_file()
    path = f"u_{update.message.from_user.id}.jpg"
    await f.download_to_drive(path)
    context.user_data['u_p'] = path
    await update.message.reply_text("এবার কাপড়ের ছবি পাঠান।")
    return CLOTH_PHOTO

async def get_cloth_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = await update.message.photo[-1].get_file()
    c_path = f"c_{update.message.from_user.id}.jpg"
    await f.download_to_drive(c_path)
    u_path = context.user_data.get('u_p')
    msg = await update.message.reply_text("⏳ AI কাজ করছে... ১ মিনিট অপেক্ষা করুন।")
    
    try:
        client = Client("yisol/IDM-VTON")
        res = client.predict(
            dict={"background": handle_file(u_path), "layers": [], "composite": None},
            garm_img=handle_file(c_path),
            garment_des="outfit",
            is_checked=True, denoise_steps=30, seed=42
        )
        user_credits[update.effective_user.id] -= 1
        await update.message.reply_photo(photo=open(res[0], 'rb'), caption="✅ ড্রেসিং সম্পন্ন!")
    except Exception as e:
        await update.message.reply_text(f"ভুল: {e}")
    finally:
        if os.path.exists(u_path): os.remove(u_path)
        if os.path.exists(c_path): os.remove(c_path)
        await msg.delete()
    return ConversationHandler.END

def main():
    threading.Thread(target=run_port_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^👕 Start Dressing$'), start_dressing)],
        states={USER_PHOTO: [MessageHandler(filters.PHOTO, get_user_photo)],
                CLOTH_PHOTO: [MessageHandler(filters.PHOTO, get_cloth_photo)]},
        fallbacks=[CommandHandler("start", start)])

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add", add_credit))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Admin Panel$'), admin_panel))
    app.add_handler(MessageHandler(filters.Regex('^📊 Balance'), lambda u, c: u.message.reply_text(f"ব্যালেন্স: {user_credits.get(u.effective_user.id, 0)}")))
    app.add_handler(conv)
    
    app.run_polling()

if __name__ == '__main__':
    main()
