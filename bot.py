import telebot
from config import BOT_TOKEN
from handlers.commands import register_handlers
from database.db import Database
from services.scheduler import start_scheduler, send_daily_reminders

bot = telebot.TeleBot(BOT_TOKEN)
register_handlers(bot)

db = Database()

if __name__ == "__main__":
    # Запуск планировщика напоминаний
    start_scheduler(lambda: send_daily_reminders(bot, db))
    bot.polling(none_stop=True)