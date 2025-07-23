from .base_state import BaseState
from utils.validators import validate_word_input, sanitize_input
from telebot import types

class WritingState(BaseState):
    @staticmethod
    def enter(bot, message, user, db):
        if user.user_id not in getattr(bot, 'user_states', {}):
            if hasattr(bot, 'user_states'):
                bot.user_states[user.user_id] = WritingState()
            else:
                from handlers.commands import user_states
                user_states[user.user_id] = WritingState()
        # Добавляем клавиатуру с кнопками перехода
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь")
        )
        bot.send_message(message.chat.id, 'Введите чешское слово и перевод через пробел:', reply_markup=markup)

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
            WritingState.enter(bot, message, user, db)
            return
        elif message.text == "Обратная связь":
            from handlers.feedback import handle_feedback_message
            handle_feedback_message(bot, message, db)
            return
        text = message.text.strip()
        if not validate_word_input(text):
            bot.send_message(message.chat.id, 'Введите слово в формате: чешское_слово перевод')
            return
        cz_word, ru_word = text.split(maxsplit=1)
        cz_word = sanitize_input(cz_word)
        ru_word = sanitize_input(ru_word)
        db.add_word(user.user_id, cz_word, ru_word)
        bot.send_message(message.chat.id, f'Слово "{cz_word} - {ru_word}" добавлено! Введите следующее или /waiting для выхода.')
        # Повторно показываем клавиатуру
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь")
        )
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup) 