from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os
from datetime import datetime
import pytz

# Токен и настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_STATUS = {}  # {chat_id: has_taken_pills_today}
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    USER_STATUS[chat_id] = False
    context.bot_data["chat_id"] = chat_id
    await update.message.reply_text(
        "Привет! Я буду напоминать тебе про таблетки. Нажми '✅Да, выпила', когда примешь таблетки."
    )

# Клавиатура с кнопкой
def get_keyboard():
    keyboard = [[InlineKeyboardButton("✅Да, выпила", callback_data="took_pills")]]
    return InlineKeyboardMarkup(keyboard)

# Функция отправки напоминания
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.bot_data.get("chat_id")
    if not chat_id:
        print("Chat ID не установлен")
        return
    if USER_STATUS.get(chat_id, False):
        return
    await context.bot.send_message(
        chat_id=chat_id,
        text="Привет, ты выпила таблетки?",
        reply_markup=get_keyboard()
    )

# Обработчик нажатия на кнопку
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    if query.data == "took_pills":
        USER_STATUS[chat_id] = True
        await query.message.reply_text("Отлично, ты выпила таблетки! Напомню завтра.")

# Сброс статуса каждый день
async def reset_status(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in USER_STATUS:
        USER_STATUS[chat_id] = False
    print("Статусы пользователей сброшены")

def main():
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Настраиваем планировщик
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        send_reminder,
        trigger=CronTrigger(minute="*", second="0", timezone=MOSCOW_TZ),  # Каждую минуту для теста
        args=[app]
    )
    scheduler.add_job(
        reset_status,
        trigger=CronTrigger(hour=0, minute=0, timezone=MOSCOW_TZ),
        args=[app]
    )
    scheduler.start()

    # Запускаем бота в режиме polling
    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
