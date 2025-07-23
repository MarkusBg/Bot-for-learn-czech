from apscheduler.schedulers.background import BackgroundScheduler

# job_func должен принимать bot и db

def start_scheduler(job_func):
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_func, 'cron', hour=8, minute=0)
    scheduler.start()
    return scheduler 

# Новая функция для рассылки напоминаний по времени каждого пользователя

def send_daily_reminders(bot, db):
    from datetime import datetime
    now = datetime.now().strftime('%H:%M')
    for user_id in db.get_all_users():
        reminder_time = db.get_reminder_time(user_id)
        if reminder_time == now:
            words = db.get_words(user_id, learned=0)
            if words:
                for w in words:
                    bot.send_message(user_id, f'Слово для повторения: {w[1]} — Перевод: {w[2]}')
            else:
                # Отправить только одно сообщение, не вызывать функцию повторно
                bot.send_message(user_id, 'Нет слов для повторения!') 