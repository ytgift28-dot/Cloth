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
ADMIN_ID = 6941003064 
CHANNEL_USERNAME = "@SH_tricks"
ADS_MONETAG = "https://omg10.com/4/10644374"
ADS_ADSTERRA = "https://www.effectivegatecpm.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

user_credits = {} 
USER_PHOTO, CLOTH_PHOTO = range(2)

# --- রেন্ডার পোর্ট বাইন্ডিং (Deploying সমাধান) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Live and Healthy!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f"Health check server listening on port {port}")
    server.serve_forever()

# --- অ্যাডমিন ফিচারস ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(f"👤 **অ্যাডমিন প্যানেল**\n\nমোট ইউজার: {len(user_credits)}\n\n"
                                   "/add [id] [amt] - ক্রেডিট দিতে\n/broadcast [msg] - সবাইকে জানাতে", parse_mode='Markdown')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    if not text: return
    for uid in user_credits.keys():
        try: await context.bot.send_message(chat_id=uid, text=f"📢 **নোটিশ:**\n\n{text}", parse_mode='Markdown')
        except: continue
    await update.message.reply_text("✅ মেসেজ পাঠানো হয়েছে।")

# --- বটের মূল লজিক ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_credits: user_credits[user_id] = 5
    kb = [['👕 Start Dressing'], ['💰 Get Credit', '📊 Balance']]
    if user_id == ADMIN_ID: kb.append(['⚙️ Admin Panel'])
    await update.message.reply_text(f"স্বাগতম! আপনার ব্যালেন্স: {user_credits[user_id]}", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def start_dressing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_credits.get(update.effective_user.id, 0) < 1:
        await update.message.reply_text("ক্রেডিট নেই! আগে ক্রেডিট নিন।")
        return ConversationHandler.END
    await update.message.reply_text("নিজের একটি ছবি পাঠান।")
    return USER_PHOTO

async def get_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = await update.message.photo[-1].get_file()
    path = f"u_{update.message.from_user.id}.jpg"
    await f.download_to_drive(path)
    context.user_data['u_p'] = path
    await update.message.reply_text("কাপড়ের ছবি পাঠান।")
    return CLOTH_PHOTO

async def get_cloth_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = await update.message.photo[-1].get_file()
    c_path = f"c_{update.message.from_user.id}.jpg"
    await f.download_to_drive(c_path)
    u_path = context.user_data.get('u_p')
    msg = await update.message.reply_text("⏳ AI কাজ করছে... ১ মিনিট অপেক্ষা করুন।")
    
    try:
        client = Client("yisol/IDM-VTON")
        # এপিআই প্যারামিটার আপডেট (এরর ফিক্সড)
        res = client.predict(
            dict={"background": handle_file(u_path), "layers": [], "composite": None},
            garm_img=handle_file(c_path),
            garment_des="outfit",
            is_checked=True, denoise_steps=30, seed=42
        )
        user_credits[update.effective_user.id] -= 1
        await update.message.reply_photo(photo=open(res[0], 'rb'), caption="✅ কাজ সম্পন্ন হয়েছে!")
    except Exception as e:
        await update.message.reply_text(f"ভুল: {e}")
    finally:
        if os.path.exists(u_path): os.remove(u_path)
        if os.path.exists(c_path): os.remove(c_path)
        await msg.delete()
    return ConversationHandler.END

def main():
    # রেন্ডার পোর্ট সমস্যার সমাধান
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^👕 Start Dressing$'), start_dressing)],
        states={USER_PHOTO: [MessageHandler(filters.PHOTO, get_user_photo)],
                CLOTH_PHOTO: [MessageHandler(filters.PHOTO, get_cloth_photo)]},
        fallbacks=[CommandHandler("start", start)])

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Admin Panel$'), admin_panel))
    app.add_handler(MessageHandler(filters.Regex('^📊 Balance'), lambda u, c: u.message.reply_text(f"ব্যালেন্স: {user_credits.get(u.effective_user.id, 0)}")))
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
