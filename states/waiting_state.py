from .base_state import BaseState
from telebot import types

class WaitingState(BaseState):
    @staticmethod
    def enter(bot, message, user, db):
        if user.user_id not in getattr(bot, 'user_states', {}):
            if hasattr(bot, 'user_states'):
                bot.user_states[user.user_id] = WaitingState()
            else:
                from handlers.commands import user_states
                user_states[user.user_id] = WaitingState()
        # Добавляем клавиатуру с кнопками перехода
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь"),
            types.KeyboardButton("Повторить слова"),
            types.KeyboardButton("Настроить время"),
            types.KeyboardButton("Мои слова")
        )
        bot.send_message(message.chat.id, 'Вы в режиме ожидания. Используйте "Изучать слова" для повторения или "Добавить слова" для добавления новых.\nМожете настроить время напоминания или повторить слова прямо сейчас.', reply_markup=markup)

    def handle(self, bot, message, user, db):
        if not hasattr(user, 'state_data'):
            user.state_data = {}
        # Обработка перехода между состояниями по кнопкам
        if message.text == "Изучать слова":
            from states.learning_state import LearningState
            LearningState.enter(bot, message, user, db)
            return
        elif message.text == "Ожидание":
            bot.send_message(message.chat.id, 'Вы уже в режиме ожидания.')
            return
        elif message.text == "Добавить слова":
            from states.writing_state import WritingState
            WritingState.enter(bot, message, user, db)
            return
        elif message.text == "Обратная связь":
            from handlers.feedback import handle_feedback_message
            handle_feedback_message(bot, message, db)
            return
        elif message.text == "Настроить время":
            if not hasattr(user, 'state_data'):
                user.state_data = {}
            user.state_data['set_time'] = True
            bot.send_message(message.chat.id, 'Введите время в формате HH:MM (например, 08:30)')
            return
        # Проверка временного состояния для установки времени
        if user.state_data.get('set_time'):
            time_part = message.text.strip()
            import re
            if re.match(r'^\d{2}:\d{2}$', time_part):
                db.set_reminder_time(user.user_id, time_part)
                bot.send_message(message.chat.id, f'Время напоминания успешно установлено на {time_part}!')
                user.state_data.pop('set_time')
            else:
                bot.send_message(message.chat.id, 'Введите время в формате HH:MM (например, 08:30)')
            return
        # Повторение слов по одному
        if message.text == "Повторить слова":
            words = db.get_words(user.user_id, learned=0)
            if not words:
                bot.send_message(message.chat.id, 'Нет слов для повторения!')
                user.state_data.pop('waiting_words', None)
                user.state_data.pop('waiting_index', None)
                user.state_data.pop('waiting_word', None)
                return
            user.state_data['waiting_words'] = words
            user.state_data['waiting_index'] = 0
            word = words[0]
            user.state_data['waiting_word'] = word
            bot.send_message(message.chat.id, f'Переведите: {word[1]}')
            return
        # Логика проверки ответа при повторении
        if user.state_data.get('waiting_word'):
            word = user.state_data['waiting_word']
            answer = message.text.strip().lower()
            correct = word[2].strip().lower() == answer
            if correct:
                bot.send_message(message.chat.id, 'Верно!')
                # Следующее слово
                user.state_data['waiting_index'] += 1
                words = user.state_data['waiting_words']
                if user.state_data['waiting_index'] < len(words):
                    next_word = words[user.state_data['waiting_index']]
                    user.state_data['waiting_word'] = next_word
                    bot.send_message(message.chat.id, f'Переведите: {next_word[1]}')
                else:
                    bot.send_message(message.chat.id, 'Все слова повторены! Молодец!')
                    user.state_data.pop('waiting_word', None)
                    user.state_data.pop('waiting_words', None)
                    user.state_data.pop('waiting_index', None)
            else:
                bot.send_message(message.chat.id, 'Неверно, попробуйте ещё раз!')
            return
        elif message.text.lower() == "мои слова":
            words = db.get_words(user.user_id, learned=0)
            if not words:
                bot.send_message(message.chat.id, 'Нет слов для повторения!')
            else:
                msg = '\n'.join([f"{i+1}: {w[1]} — {w[2]}" for i, w in enumerate(words)])
                bot.send_message(message.chat.id, f'Ваши слова для повторения:\n{msg}\nЧтобы удалить слово, напишите: Удалить слово <номер>')
            user.state_data['words_for_delete'] = words
            return
        elif message.text.lower().startswith("удалить слово"):
            parts = message.text.strip().split()
            if len(parts) == 3 and parts[2].isdigit():
                idx = int(parts[2]) - 1
                words = user.state_data.get('words_for_delete')
                if words and 0 <= idx < len(words):
                    word_id = words[idx][0]
                    db.delete_word(word_id)
                    bot.send_message(message.chat.id, f'Слово под номером {idx+1} удалено.')
                else:
                    bot.send_message(message.chat.id, 'Нет слова с таким номером.')
            else:
                bot.send_message(message.chat.id, 'Используйте формат: Удалить слово <номер>')
            return
        # Показываем клавиатуру с дополнительными кнопками
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь"),
            types.KeyboardButton("Повторить слова"),
            types.KeyboardButton("Настроить время"),
            types.KeyboardButton("Мои слова")
        )
        bot.send_message(message.chat.id, 'Вы в режиме ожидания. Используйте "Изучать слова" для повторения или "Добавить слова" для добавления новых.\nМожете настроить время напоминания или повторить слова прямо сейчас.', reply_markup=markup) 