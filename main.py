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
TOKEN = "8629018568:AAGQwHKPMf6kNuvWWdmCpXw1d_qmxCh06SE"
ADMIN_ID = 6941003064 
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
        self.wfile.write(b"Bot is Running!")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- অ্যাডমিন কমান্ডস ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = (f"👤 **অ্যাডমিন প্যানেল**\n\n"
           f"মোট ইউজার: {len(user_credits)}\n"
           f"ক্রেডিট দিতে: `/add ইউজার_আইডি পরিমাণ` (যেমন: `/add 12345 10`)\n"
           f"সবাইকে মেসেজ দিতে: `/broadcast আপনার মেসেজ`")
    await update.message.reply_text(msg, parse_mode='Markdown')

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        user_credits[target_id] = user_credits.get(target_id, 0) + amount
        await update.message.reply_text(f"✅ ইউজার `{target_id}` কে {amount} ক্রেডিট দেওয়া হয়েছে।", parse_mode='Markdown')
        await context.bot.send_message(chat_id=target_id, text=f"🎁 অ্যাডমিন আপনাকে {amount} ক্রেডিট দিয়েছে!")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! এভাবে লিখুন: `/add 123456 10`", parse_mode='Markdown')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("❌ মেসেজটি লিখুন। উদাহরণ: `/broadcast হ্যালো ইউজারস`")
        return
    
    count = 0
    for uid in list(user_credits.keys()):
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **অ্যাডমিন নোটিশ:**\n\n{message_text}", parse_mode='Markdown')
            count += 1
        except: continue
    await update.message.reply_text(f"✅ {count} জন ইউজারকে মেসেজ পাঠানো হয়েছে।")

# --- মূল ফাংশনসমূহ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_credits: user_credits[user_id] = 5
    
    kb = [['👕 Start Dressing'], ['💰 Get Credit', '📊 Balance']]
    if user_id == ADMIN_ID: kb.append(['⚙️ Admin Panel'])
    
    await update.message.reply_text(f"ব্যালেন্স: {user_credits[user_id]} ক্রেডিট।", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def get_credit_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn = [[InlineKeyboardButton("Ad 1 (Monetag)", url=ADS_MONETAG)],
           [InlineKeyboardButton("Ad 2 (Adsterra)", url=ADS_ADSTERRA)],
           [InlineKeyboardButton("Claim Credit ✅", callback_data="claim_credit")]]
    await update.message.reply_text("নিচের বাটনগুলো থেকে অ্যাড দেখে ক্রেডিট ক্লেইম করুন।", reply_markup=InlineKeyboardMarkup(btn))

async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    user_credits[uid] = user_credits.get(uid, 0) + 1
    await query.edit_message_text(f"১ ক্রেডিট যোগ হয়েছে! বর্তমান ব্যালেন্স: {user_credits[uid]}")

# --- ড্রেসিং কনভারসেশন ---
async def start_dressing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_credits.get(update.effective_user.id, 0) < 1:
        await update.message.reply_text("ক্রেডিট নেই!")
        return ConversationHandler.END
    await update.message.reply_text("নিজের একটি পরিষ্কার ছবি পাঠান।")
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
    msg = await update.message.reply_text("⏳ AI কাজ করছে...")
    
    try:
        client = Client("yisol/IDM-VTON")
        res = client.predict(dict={"background": handle_file(u_path), "layers": [], "composite": None},
                             garm_img=handle_file(c_path), garment_des="outfit",
                             is_checked=True, denoise_steps=30, seed=42)
        user_credits[update.effective_user.id] -= 1
        await update.message.reply_photo(photo=open(res[0], 'rb'), caption="✅ সম্পন্ন!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
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

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_credit))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Regex('^💰 Get Credit$'), get_credit_msg))
    app.add_handler(MessageHandler(filters.Regex('^📊 Balance$'), lambda u, c: u.message.reply_text(f"ব্যালেন্স: {user_credits.get(u.effective_user.id, 0)}")))
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Admin Panel$'), admin_panel))
    app.add_handler(CallbackQueryHandler(claim_callback, pattern="claim_credit"))
    app.add_handler(conv)
    
    app.run_polling()

if __name__ == '__main__':
    main()
