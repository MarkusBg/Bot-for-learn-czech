from .base_state import BaseState
from services.learning import get_next_word, check_answer
from telebot import types

class LearningState(BaseState):
    @staticmethod
    def enter(bot, message, user, db):
        if user.user_id not in getattr(bot, 'user_states', {}):
            if hasattr(bot, 'user_states'):
                bot.user_states[user.user_id] = LearningState()
            else:
                # fallback for global user_states
                from handlers.commands import user_states
                user_states[user.user_id] = LearningState()
        if not hasattr(user, 'state_data'):
            user.state_data = {}
        user_states = getattr(bot, 'user_states', None)
        if user_states is None:
            from handlers.commands import user_states as global_user_states
            user_states = global_user_states
        # Добавляем клавиатуру с кнопками перехода
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("Изучать слова"),
            types.KeyboardButton("Ожидание"),
            types.KeyboardButton("Добавить слова"),
            types.KeyboardButton("Обратная связь"),
            types.KeyboardButton("Мои слова")
        )
        bot.send_message(message.chat.id, "Вы в режиме изучения слов. Выберите действие:", reply_markup=markup)

    def handle(self, bot, message, user, db):
        # Обработка перехода между состояниями по кнопкам
        if message.text == "Изучать слова":
            bot.send_message(message.chat.id, 'Вы уже в режиме изучения слов.')
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
            from handlers.feedback import handle_feedback_message
            handle_feedback_message(bot, message, db)
            return
        elif message.text.lower() == "мои слова":
            words = db.get_words(user.user_id, learned=0)
            if not words:
                bot.send_message(message.chat.id, 'Нет слов для изучения!')
            else:
                msg = '\n'.join([f"{i+1}: {w[1]} — {w[2]}" for i, w in enumerate(words)])
                bot.send_message(message.chat.id, f'Ваши слова для изучения:\n{msg}\nЧтобы удалить слово, напишите: Удалить слово <номер>')
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
        state_data = getattr(user, 'state_data', {})
        if 'current_word' not in state_data:
            word = get_next_word(user.user_id, db)
            if not word:
                bot.send_message(message.chat.id, 'Нет слов для изучения. Добавьте новые через /writing.')
                return
            state_data['current_word'] = word
            bot.send_message(message.chat.id, f'Переведите: {word[1]}')
            user.state_data = state_data
            return
        word = state_data['current_word']
        if check_answer(user.user_id, word[0], message.text, db):
            bot.send_message(message.chat.id, 'Верно!')
            state_data.pop('current_word')
            # Следующее слово
            next_word = get_next_word(user.user_id, db)
            if next_word:
                state_data['current_word'] = next_word
                bot.send_message(message.chat.id, f'Переведите: {next_word[1]}')
            else:
                bot.send_message(message.chat.id, 'Все слова повторены! Молодец!')
        else:
            bot.send_message(message.chat.id, 'Неверно, попробуйте ещё раз!') 