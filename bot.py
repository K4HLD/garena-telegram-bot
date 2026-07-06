import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from playwright.async_api import async_playwright

FIXED_USER = "k4hld999"
FIXED_PASS = "K4hld@garena99"
GARENA_URL = "https://auth.garena.com/universal/register"

TOKEN = "8808965113:AAGKNcrlzHdoJoixnxuNf_q24IPU_7ZTeDM"   # <-- تأكد من التوكن الجديد
SUBSCRIBERS = [7014840619, 7294246161]

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in SUBSCRIBERS:
        await update.message.reply_text(
            f"❌ هذا البوت مدفوع يرجى التواصل مع المطور لتفعيل اشتراكك @k4h_d وخاص بتفعيل سيرفر استعادة فري فاير.\nالـ ID الخاص بك: `{user_id}`",
            parse_mode="Markdown"
        )
        return
    await update.message.reply_text("✅ حسابك مفعل. أرسل الآن بريد الاستعادة Gmail لي فيه المشكل *البريد فقط بدون كلمة سر.")

async def handle_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in SUBSCRIBERS:
        return

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
    if not gmail:
        return

    await query.edit_message_text("⏳ جاري الاتصال بالسيرفر وتفعيل نظام الاستعادة... يرجى الانتظار ثواني.")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1280, "height": 720})

            await page.goto(GARENA_URL, timeout=90000, wait_until="load")
            await asyncio.sleep(4)

            # 1. ملء الخانات
            inputs = await page.query_selector_all("input")
            if len(inputs) >= 4:
                await inputs[0].fill(FIXED_USER)
                await inputs[1].fill(FIXED_PASS)
                await inputs[2].fill(FIXED_PASS)
                await inputs[3].fill(gmail)

            # 2. الضغط على زر التسجيل
            register_btn = page.locator(
                "button:has-text('سجل الآن'), button:has-text('Register Now'), button:has-text('Sign Up'), button:has-text('تسجيل')"
            ).first
            if await register_btn.count() > 0:
                await register_btn.click(force=True)
                # انتظار ظهور زر إرسال الرمز
                await page.wait_for_selector(
                    "button:has-text('GET CODE'), button:has-text('Send Code'), button:has-text('أرسل الرمز'), button:has-text('إرسال الرمز')",
                    timeout=20000
                )
                await asyncio.sleep(2)

            # 3. الضغط على إرسال الرمز
            get_code_button = page.locator(
                "button:has-text('GET CODE'), button:has-text('Send Code'), button:has-text('أرسل الرمز'), button:has-text('إرسال الرمز')"
            ).first
            await get_code_button.wait_for(state="visible", timeout=10000)
            await get_code_button.click(force=True)

            await asyncio.sleep(5)
            await browser.close()

            success_text = (
                "✅ **تمت العملية بنجاح!**\n\n"
                "تم تفعيل السيرفر وإرسال الرمز بنجاح. تفقد (البريد الوارد أو المهملات Spams) في الـ Gmail الخاص بك الآن، "
                "وستجد الرمز حطه مكان الرمز في اللعبة واعمل تحقق مباشرة بدون الضغط على ارسال ❌."
            )
            await query.message.reply_text(success_text, parse_mode="Markdown")

    except Exception as e:
        print(f"Error details: {e}")
        await query.message.reply_text("❌ عذراً، حدث ضغط على السيرفر. يرجى المحاولة مرة أخرى بعد دقيقة.")

# --- إعداد Webhook وبدء الخادم ---
async def healthcheck(request):
    """مسار فحص الصحة لـ Render"""
    return web.Response(text="⚡ System Active")

def main():
    # 1. إنشاء التطبيق
    app = Application.builder().token(TOKEN).build()

    # 2. إضافة handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gmail))
    app.add_handler(CallbackQueryHandler(button_click))

    # 3. إعداد aiohttp server لاستقبال الطلبات
    aiohttp_app = web.Application()
    aiohttp_app.router.add_get('/', healthcheck)      # لفحص الصحة
    # استخدام create_webhook_handler للحصول على handler متوافق مع aiohttp
    webhook_handler = app.create_webhook_handler()
    aiohttp_app.router.add_post('/webhook', webhook_handler)

    # 4. تعيين Webhook على تيليجرام
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')  # Render يوفره تلقائياً
    if not RENDER_URL:
        raise ValueError("يجب تشغيل البوت على Render أو تحديد RENDER_EXTERNAL_URL")
    webhook_url = f"https://{RENDER_URL}/webhook"

    # نستخدم asyncio لتعيين الـ webhook قبل تشغيل الخادم
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.bot.set_webhook(url=webhook_url))
    print(f"✅ تم تعيين Webhook على: {webhook_url}")

    # 5. تشغيل الخادم
    port = int(os.environ.get('PORT', 10000))
    web.run_app(aiohttp_app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()