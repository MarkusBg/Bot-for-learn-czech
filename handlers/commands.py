from telebot import types
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import Database
from services.user_state import get_user_state, set_user_state
from states.writing_state import WritingState
from states.learning_state import LearningState
from states.waiting_state import WaitingState
from handlers.feedback import handle_feedback_message, FeedbackState
from database.models import User

# Глобальный объект базы (можно заменить на DI)
db = Database()

user_states = {}


def get_or_create_user(user_id):
    db.register_user(user_id)
    state = db.get_user_state(user_id)
    return User(user_id, state)


def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Изучать слова"),
        types.KeyboardButton("Ожидание"),
        types.KeyboardButton("Добавить слова"),
        types.KeyboardButton("Обратная связь"),
        types.KeyboardButton("/help")
    )
    return markup


def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def handle_start(message: Message):
        user = get_or_create_user(message.from_user.id)
        markup = get_main_keyboard()
        bot.send_message(message.chat.id, 'Добро пожаловать в бота для изучения Чешского!\nНажмите кнопку ниже для выбора действия.', reply_markup=markup)
        set_user_state(user.user_id, 'waiting', db)

    @bot.message_handler(commands=['help'])
    def handle_help(message: Message):
        markup = get_main_keyboard()
        bot.send_message(message.chat.id, 'Все команды бота:\nИзучать слова — начать изучение слов\nДобавить слова — добавить слова\nОжидание — режим изучения слов каждое утро\nОбратная связь — оставить обратную связь\nЧто будем делать дальше?', reply_markup=markup)


    @bot.message_handler(func=lambda message: message.text in ["Изучать слова", "Добавить слова", "Ожидание", "Обратная связь"])
    def handle_main_menu_choice(message: Message):
        user = get_or_create_user(message.from_user.id)
        remove_markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Переходим...", reply_markup=remove_markup)
        if message.text == "Изучать слова":
            LearningState.enter(bot, message, user, db)
            # Сразу запускаем handle для показа слова и проверки ответа
            if user.user_id not in user_states:
                user_states[user.user_id] = LearningState()
            user_states[user.user_id].handle(bot, message, user, db)
            return
        elif message.text == "Добавить слова":
            WritingState.enter(bot, message, user, db)
        elif message.text == "Ожидание":
            WaitingState.enter(bot, message, user, db)
        elif message.text == "Обратная связь":
            FeedbackState.enter(bot, message, user, db)


    @bot.message_handler(commands=['learn'])
    def handle_learn(message: Message):
        user = get_or_create_user(message.from_user.id)
        set_user_state(user.user_id, 'learning', db)
        user_states[user.user_id] = LearningState()
        user.state_data = {}
        user_states[user.user_id].handle(bot, message, user, db)
        bot.edit_message_reply_markup(reply_markup=None)

    @bot.message_handler(commands=['writing'])
    def handle_writing(message: Message):
        user = get_or_create_user(message.from_user.id)
        set_user_state(user.user_id, 'writing', db)
        user_states[user.user_id] = WritingState()
        bot.send_message(message.chat.id, 'Введите чешское слово и перевод через пробел:')

    @bot.message_handler(commands=['waiting'])
    def handle_waiting(message: Message):
        user = get_or_create_user(message.from_user.id)
        set_user_state(user.user_id, 'waiting', db)
        user_states[user.user_id] = WaitingState()
        user_states[user.user_id].handle(bot, message, user, db)

    @bot.message_handler(commands=['feedback'])
    def handle_feedback(message: Message):
        user = get_or_create_user(message.from_user.id)
        FeedbackState.enter(bot, message, user, db)

    @bot.message_handler(func=lambda m: True)
    def handle_any(message: Message):
        user = get_or_create_user(message.from_user.id)
        state = db.get_user_state(user.user_id)
        if state == 'writing':
            if user.user_id not in user_states:
                user_states[user.user_id] = WritingState()
            user_states[user.user_id].handle(bot, message, user, db)
        elif state == 'learning':
            if user.user_id not in user_states:
                user_states[user.user_id] = LearningState()
            if not hasattr(user, 'state_data'):
                user.state_data = {}
            user_states[user.user_id].handle(bot, message, user, db)
        elif state == 'feedback':
            if user.user_id not in user_states:
                user_states[user.user_id] = FeedbackState()
            user_states[user.user_id].handle(bot, message, user, db)
        else:
            if user.user_id not in user_states:
                user_states[user.user_id] = WaitingState()
            user_states[user.user_id].handle(bot, message, user, db) 