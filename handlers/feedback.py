from database.db import Database
from telebot.types import Message
from telebot import types

class FeedbackState:
    @staticmethod
    def enter(bot, message, user, db):
        # Клавиатура переходов
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь")
        )
        bot.send_message(message.chat.id, '✍️ Напиши, пожалуйста, свой отзыв:', reply_markup=markup)
        # Сохраняем состояние пользователя, если нужно
        user.state = 'feedback'
        if hasattr(bot, 'user_states'):
            bot.user_states[user.user_id] = FeedbackState()
        else:
            from handlers.commands import user_states
            user_states[user.user_id] = FeedbackState()

    def handle(self, bot, message, user, db):
        # Обработка перехода между состояниями по кнопкам
        if message.text == "Изучать слова":
            from states.learning_state import LearningState
            LearningState.enter(bot, message, user, db)
            return
        elif message.text == "Ожидание":
            from states.waiting_state import WaitingState
            WaitingState.enter(bot, message, user, db)
            return
        elif message.text == "Добавить слова":
            from states.writing_state import WritingState
            WritingState.enter(bot, message, user, db)
            return
        elif message.text == "Обратная связь":
            FeedbackState.enter(bot, message, user, db)
            return
        # Сохраняем отзыв
        db.save_feedback(message.from_user.id, message.text)
        bot.send_message(message.chat.id, 'Спасибо за ваш отзыв!')
        # Снова показываем клавиатуру переходов
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь")
        )
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

# Старый обработчик (оставлен для совместимости, если где-то вызывается напрямую)
def handle_feedback_message(bot, message: Message, db: Database):
    db.save_feedback(message.from_user.id, message.text)
    bot.send_message(message.chat.id, 'Спасибо за ваш отзыв!') 

# def save_review(user_id, username, text):
#     conn = sqlite3.connect("bot.db")
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO reviews (user_id, username, review) VALUES (?, ?, ?)",
#                    (user_id, username, text))
#     conn.commit()
#     conn.close()