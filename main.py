import os
import asyncio
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from gradio_client import Client, handle_file

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = "8629018568:AAGJMsqrWUSwmsvRZrF0IfXCnb2vwrMWMcE"
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks"
ADS_MONETAG = "https://omg10.com/4/10644374"
ADS_ADSTERRA = "https://www.effectivegatecpm.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

user_credits = {} 
USER_PHOTO, CLOTH_PHOTO = range(2)

# Render Health Check (বট অনলাইন রাখার জন্য)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Force Join Check
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=update.effective_user.id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_credits: user_credits[user_id] = 0
    
    if not await is_subscribed(update, context):
        btn = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/SH_tricks")],
               [InlineKeyboardButton("Joined ✅", callback_data="check_join")]]
        await update.message.reply_text("বটটি ব্যবহার করতে আগে আমাদের চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(btn))
        return

    kb = [['👕 Start Dressing'], ['💰 Get Credit', '📊 Balance']]
    await update.message.reply_text(f"স্বাগতম! আপনার ব্যালেন্স: {user_credits[user_id]}", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def get_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Ad 1", url=ADS_MONETAG), InlineKeyboardButton("Ad 2", url=ADS_ADSTERRA)],
                [InlineKeyboardButton("Claim 1 Credit ✅", callback_data="claim")]]
    await update.message.reply_text("অ্যাড দেখে ক্রেডিট ক্লেইম করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_credits[query.from_user.id] = user_credits.get(query.from_user.id, 0) + 1
    await query.edit_message_text(f"সফল! বর্তমান ব্যালেন্স: {user_credits[query.from_user.id]}")

async def start_dressing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_credits.get(update.effective_user.id, 0) < 1:
        await update.message.reply_text("ক্রেডিট নেই! অ্যাড দেখে ক্রেডিট নিন।")
        return ConversationHandler.END
    await update.message.reply_text("আপনার নিজের একটি পরিষ্কার ছবি পাঠান।")
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
    msg = await update.message.reply_text("⏳ AI কাজ করছে... অপেক্ষা করুন।")
    try:
        client = Client("yisol/IDM-VTON")
        res = client.predict(dict={"background": handle_file(u_path), "layers": [], "composite": None},
                             garm_img=handle_file(c_path), garment_des="outfit",
                             is_checked=True, is_checked_det=True, denoise_steps=30, seed=42, api_name="/process")
        user_credits[update.effective_user.id] -= 1
        await update.message.reply_photo(photo=open(res[0], 'rb'), caption="✅ সম্পন্ন!")
    except Exception as e: await update.message.reply_text(f"Error: {e}")
    finally:
        if os.path.exists(u_path): os.remove(u_path)
        if os.path.exists(c_path): os.remove(c_path)
        await msg.delete()
    return ConversationHandler.END

def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^👕 Start Dressing$'), start_dressing)],
        states={USER_PHOTO: [MessageHandler(filters.PHOTO, get_user_photo)],
                CLOTH_PHOTO: [MessageHandler(filters.PHOTO, get_cloth_photo)]},
        fallbacks=[CommandHandler("start", start)])
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(claim_callback, pattern="claim"))
    app.add_handler(MessageHandler(filters.Regex('^💰 Get Credit'), get_credit))
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
