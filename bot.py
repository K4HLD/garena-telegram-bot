import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from playwright.async_api import async_playwright

FIXED_USER = "k4hld999"
FIXED_PASS = "K4hld@garena99"
GARENA_URL = "https://auth.garena.com/universal/register"

TOKEN = "8627196820:AAEnVeL2zFhapb-1AU70ENSDUoa6Od7xgXg" 
SUBSCRIBERS = [8627196820, 7014840619]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in SUBSCRIBERS:
        await update.message.reply_text(f"❌ هاد البوت مدفوع وخاص بتفعيل سيرفر استعادة فري فاير.\nالـ ID الخاص بك: `{user_id}`", parse_mode="Markdown")
        return
    await update.message.reply_text("✅ حسابك مفعل. أرسل الآن بريد الاستعادة (Gmail) لي فيه المشكل.")

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in SUBSCRIBERS: return

    gmail = update.message.text.strip()
    if "@" not in gmail or "." not in gmail:
        await update.message.reply_text("❌ المرجو إرسال بريد إلكتروني صحيح.")
        return

    context.user_data['current_gmail'] = gmail

    keyboard = [[InlineKeyboardButton("تم ✅", callback_data="run_process")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    instruction_text = (
        "⚠️ **تعليمات مهمة جداً:**\n\n"
        "1️⃣ حط جمايل الاستعادة في مكان استعادة الحساب او تغيير/الغاء ربط الاستعادة داخل اللعبة.\n"
        "2️⃣ **تنبيه:** لا تضغط على ارسال ❌ داخل اللعبة.\n"
        "3️⃣ ارجع هنا واضغط على زر **تم** أسفله مباشرة."
    )
    await update.message.reply_text(instruction_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    gmail = context.user_data.get('current_gmail')
    if not gmail: return

    await query.edit_message_text("⏳ جاري الاتصال بالسيرفر وتفعيل نظام الاستعادة... يرجى الانتظار ثواني.")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"])
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1280, "height": 720})
            
            await page.goto(GARENA_URL, timeout=60000)
            await page.wait_for_load_state("networkidle")

            inputs = await page.query_selector_all("input")
            await inputs[0].fill(FIXED_USER)
            await inputs[1].fill(FIXED_PASS)
            await inputs[2].fill(FIXED_PASS)
            await inputs[3].fill(gmail)
            
            get_code_button = page.locator("text=GET CODE").or_(page.locator("button:has-text('GET CODE')")).first
            await get_code_button.click()
            await asyncio.sleep(5)
            await browser.close()
            
            success_text = (
                "✅ **تمت العملية بنجاح!**\n\n"
                "تم تفعيل السيرفر وإرسال الرمز بنجاح. تفقد علامة التبويب (البريد الوارد أو المهملات Spams) في الـ Gmail الخاص بك الآن، وستجد الرمز شغالاً."
            )
            await query.message.reply_text(success_text, parse_mode="Markdown")
    except Exception as e:
        await query.message.reply_text("❌ عذراً، حدث ضغط على السيرفر. يرجى المحاولة مرة أخرى بعد دقيقة.")

def main():
    # كود الـ Flask الأساسي لمنع توقف السيرفر المجاني
    from flask import Flask
    import threading
    app_flask = Flask('')
    @app_flask.route('/')
    def home(): return "⚡ System Active"
    def run(): app_flask.run(host='0.0.0.0', port=7860)
    threading.Thread(target=run).start()

    # إنشاء التطبيق بالطريقة الرسمية والمستقرة
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gmail))
    app.add_handler(CallbackQueryHandler(button_click))
    
    # تشغيل البوت مع إعدادات حماية مدمجة ضد انقطاع الشبكة
    app.run_polling(close_loop=False, drop_pending_updates=True)

if __name__ == "__main__":
    main()
  
