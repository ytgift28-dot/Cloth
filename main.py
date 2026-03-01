import os
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from gradio_client import Client, handle_file

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = "8629018568:AAGODbfefbVEc3QFwniepBMNhXmZ4cTbhiQ"
HF_TOKEN = os.environ.get("HF_TOKEN")" 
ADMIN_ID = 6941003064 
CHANNEL_USERNAME = "@SH_tricks"
ADS_MONETAG = "https://omg10.com/4/10644374"
ADS_ADSTERRA = "https://www.effectivegatecpm.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

# ডাটা ডিকশনারি
user_credits = {} 
user_vip = {}       
user_click_time = {} 
daily_checkin = {}  
is_maintenance = False 
active_tasks = 0      

USER_PHOTO, CLOTH_PHOTO = range(2)

# --- Render Port Binding ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SH Photo AI is running with Token Support!")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- অ্যাডমিন কমান্ডস ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    mode_status = "🔴 ON" if is_maintenance else "🟢 OFF"
    msg = (f"👤 **অ্যাডমিন প্যানেল**\n\n"
           f"মেইনটেন্যান্স মোড: {mode_status}\n"
           f"মোট ইউজার: {len(user_credits)}\n\n"
           f"🔹 `/mode` - মেইনটেন্যান্স অন/অফ\n"
           f"🔹 `/setvip id` - ভিআইপি দিতে\n"
           f"🔹 `/add id amount` - ক্রেডিট দিতে\n"
           f"🔹 `/broadcast msg` - ব্রডকাস্ট")
    await update.message.reply_text(msg, parse_mode='Markdown')

async def toggle_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_maintenance
    if update.effective_user.id != ADMIN_ID: return
    is_maintenance = not is_maintenance
    status = "চালু" if is_maintenance else "বন্ধ"
    await update.message.reply_text(f"✅ মেইনটেন্যান্স মোড {status} করা হয়েছে।")

async def set_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0])
        user_vip[uid] = True
        await update.message.reply_text(f"🌟 ইউজার `{uid}` এখন VIP সদস্য।")
    except: await update.message.reply_text("ব্যবহার: `/setvip 12345`")

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        user_credits[target_id] = user_credits.get(target_id, 0) + amount
        await update.message.reply_text(f"✅ {amount} ক্রেডিট দেওয়া হয়েছে।")
    except: await update.message.reply_text("ব্যবহার: `/add 12345 10`")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    if not text: return
    for uid in list(user_credits.keys()):
        try: await context.bot.send_message(chat_id=uid, text=f"📢 **নোটিশ:**\n\n{text}", parse_mode='Markdown')
        except: continue
    await update.message.reply_text("✅ ব্রডকাস্ট সম্পন্ন।")

# --- মূল ফাংশনসমূহ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_maintenance and user_id != ADMIN_ID:
        await update.message.reply_text("⚠️ দুঃখিত, বট বর্তমানে মেইনটেন্যান্স মোডে আছে।")
        return

    if context.args and context.args[0].isdigit():
        ref = int(context.args[0])
        if ref != user_id and user_id not in user_credits:
            user_credits[ref] = user_credits.get(ref, 0) + 2
            await context.bot.send_message(chat_id=ref, text="🎁 রেফারেল বোনাস: ২ ক্রেডিট যোগ হয়েছে!")

    if user_id not in user_credits: user_credits[user_id] = 5
    kb = [['👕 Start Dressing'], ['💰 Get Credit', '📊 Balance'], ['🎁 Daily Bonus', '🔗 Referral']]
    if user_id == ADMIN_ID: kb.append(['⚙️ Admin Panel'])
    await update.message.reply_text(f"ব্যালেন্স: {user_credits[user_id]} ক্রেডিট।", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = time.strftime("%Y-%m-%d")
    if daily_checkin.get(uid) == today:
        await update.message.reply_text("❌ আজকে নেওয়া হয়েছে। আগামীকাল আসুন।")
    else:
        daily_checkin[uid] = today
        user_credits[uid] = user_credits.get(uid, 0) + 1
        await update.message.reply_text("✅ ১ ক্রেডিট বোনাস পেলেন।")

async def get_credit_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_vip:
        await update.message.reply_text("🌟 আপনি VIP! আপনার অ্যাড লাগবে না।")
        return
    user_click_time[uid] = time.time()
    btn = [[InlineKeyboardButton("Ad 1", url=ADS_MONETAG)], [InlineKeyboardButton("Ad 2", url=ADS_ADSTERRA)],
           [InlineKeyboardButton("Claim ✅", callback_data="claim_verify")]]
    await update.message.reply_text("অ্যাডে ক্লিক করে ২০ সেকেন্ড পর Claim দিন।", reply_markup=InlineKeyboardMarkup(btn))

async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    elapsed = time.time() - user_click_time.get(uid, 0)
    if elapsed < 20:
        await query.answer(f"অপেক্ষা করুন: {int(20-elapsed)}s", show_alert=True)
    else:
        await query.answer()
        user_credits[uid] = user_credits.get(uid, 0) + 1
        await query.edit_message_text(f"✅ ক্রেডিট যোগ হয়েছে। ব্যালেন্স: {user_credits[uid]}")

async def referral_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot = await context.bot.get_me()
    await update.message.reply_text(f"🔗 রেফারেল লিংক:\nhttps://t.me/{bot.username}?start={uid}")

# --- ড্রেসিং ও স্মার্ট কিউ ---
async def start_dressing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_maintenance and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ মেইনটেন্যান্স চলছে।")
        return ConversationHandler.END
    if update.effective_user.id not in user_vip and user_credits.get(update.effective_user.id, 0) < 1:
        await update.message.reply_text("❌ ক্রেডিট নেই।")
        return ConversationHandler.END
    await update.message.reply_text("নিজের পরিষ্কার ছবি পাঠান।")
    return USER_PHOTO

async def get_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = await update.message.photo[-1].get_file()
    path = f"u_{update.message.from_user.id}.jpg"
    await f.download_to_drive(path)
    context.user_data['u_p'] = path
    await update.message.reply_text("এবার কাপড়ের ছবি পাঠান।")
    return CLOTH_PHOTO

async def get_cloth_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_tasks
    f = await update.message.photo[-1].get_file()
    c_path = f"c_{update.message.from_user.id}.jpg"
    await f.download_to_drive(c_path)
    u_path = context.user_data.get('u_p')
    uid = update.effective_user.id
    
    active_tasks += 1
    msg = await update.message.reply_text(f"⏳ কিউতে আপনার সিরিয়াল: {active_tasks}\nAI কাজ শুরু করেছে...")
    
    try:
        # টোকেন এখানে যুক্ত করা হয়েছে যা কোটা বাড়াবে
        client = Client("yisol/IDM-VTON", hf_token=HF_TOKEN)
        res = client.predict(dict={"background": handle_file(u_path), "layers": [], "composite": None},
                             garm_img=handle_file(c_path), garment_des="outfit",
                             is_checked=True, denoise_steps=30, seed=42)
        if uid not in user_vip: user_credits[uid] -= 1
        await update.message.reply_photo(photo=open(res[0], 'rb'), caption="✅ সম্পন্ন! @SH_tricks")
    except Exception as e:
        await update.message.reply_text(f"ভুল: {e}")
    finally:
        active_tasks -= 1
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
    app.add_handler(CommandHandler("mode", toggle_mode))
    app.add_handler(CommandHandler("add", add_credit))
    app.add_handler(CommandHandler("setvip", set_vip))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Regex('^💰 Get Credit$'), get_credit_msg))
    app.add_handler(MessageHandler(filters.Regex('^🎁 Daily Bonus$'), daily_bonus))
    app.add_handler(MessageHandler(filters.Regex('^🔗 Referral$'), referral_msg))
    app.add_handler(MessageHandler(filters.Regex('^📊 Balance$'), lambda u, c: u.message.reply_text(f"ব্যালেন্স: {user_credits.get(u.effective_user.id, 0)}")))
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Admin Panel$'), admin_panel))
    app.add_handler(CallbackQueryHandler(claim_callback, pattern="claim_verify"))
    app.add_handler(conv)
    
    app.run_polling()

if __name__ == '__main__':
    main()
