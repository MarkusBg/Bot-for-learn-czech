import tg
import telebot
from telebot import types
from transitions import Machine
from datetime import datetime, time
import time as sleep_time
import threading

bot = telebot.TeleBot(tg.token)

# Словарь для хранения состояний пользователей
user_states = {}

class LearnBot:
    states = ['start', 'writing_words', 'checking_words', 'learning_mode']
    
    transitions = [
        # Переходы из стартового состояния
        {'trigger': 'go', 'source': 'start', 'dest': 'writing_words'},
        {'trigger': 'help', 'source': 'start', 'dest': 'start'},
        
        # Переходы из состояния writing_words
        {'trigger': 'list', 'source': 'writing_words', 'dest': 'checking_words'},
        {'trigger': 'ready', 'source': 'writing_words', 'dest': 'learning_mode'},
        {'trigger': 'back', 'source': 'writing_words', 'dest': 'start'},
        
        # Переходы из состояния checking_words
        {'trigger': 'back', 'source': 'checking_words', 'dest': 'writing_words'},
        {'trigger': 'ready', 'source': 'checking_words', 'dest': 'learning_mode'},
        
        # Переходы из learning_mode
        {'trigger': 'back', 'source': 'learning_mode', 'dest': 'start'},
        {'trigger': 'back', 'source': 'learning_mode', 'dest': 'writing_words'},
        {'trigger': 'continue_learning', 'source': 'learning_mode', 'dest': 'writing_words'},
        
        # Глобальные переходы
        {'trigger': 'reset', 'source': '*', 'dest': 'start'}
    ]

class User:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.words = []
        self.current_word = None  # Текущее слово для проверки
        self.word_to_check = None  # Слово, которое нужно перевести
        
        # Инициализация машины состояний
        self.machine = Machine(model=self, states=LearnBot.states, 
                             transitions=LearnBot.transitions, initial='start')
    
    def add_word(self, czech, translation):
        if (czech, translation) not in self.words:
            self.words.append((czech, translation))
            return True
        return False
    
    def get_words_list(self):
        return '\n'.join([f'{cz} - {tr}' for cz, tr in self.words])
    
    def get_next_word(self):
        if not self.words:
            return None
        
        if self.current_word_index >= len(self.words):
            self.current_word_index = 0  # Сброс на начало списка
            
        word = self.words[self.current_word_index]
        self.current_word_index += 1
        return word
    
    def clear_words(self):
        self.words = []
        self.current_word_index = 0

def schedule_daily_messages():
    while True:
        now = datetime.now().time()
        target_time = time(7, 0)
        
        if target_time.hour == now.hour and target_time.minute == now.minute:
            send_daily_words()
            sleep_time.sleep(61)
        else:
            sleep_time.sleep(30)

def send_daily_words():
    for chat_id, user in user_states.items():
        if user.state == 'learning_mode' and user.words:
            word = user.get_next_word()
            if word:
                bot.send_message(chat_id, f"Повторите слово: {word[0]} - ?")

@bot.message_handler(commands=['clear'])
def clear_words(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/back"))
    if chat_id in user_states:
        user = user_states[chat_id]
        user.clear_words()
        bot.send_message(chat_id, '"Список слов очищен!"', reply_markup=markup)
    else:
        bot.send_message(chat_id, "У вас нет сохранённых слов.")

@bot.message_handler(commands=['start', 'reset'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    user.reset()
    
    bot.send_message(chat_id, 'Привет!')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("/help")
    markup.add(item1)
    bot.send_message(chat_id, 'Выберите что вам нужно:', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_button(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    user.help()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item2 = types.KeyboardButton("/learn")
    markup.add(item2)
    bot.send_message(chat_id, 'Этот бот создан для изучения чешских слов Марком Брагутой\n'
                     'Это кстати instagram Создателя: @MarkBragyta\n'
                     'Жмякай кнопку внизу чтобы начать', reply_markup=markup)

@bot.message_handler(commands=['learn'])
def get_words(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    user.go()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("/back")
    markup.add(item1)
    bot.send_message(chat_id, 'Отлично, давай начнём.\n'
                     'Вы будете присылать мне слова в таком порядке:\n'
                     '"české slovo" - "его перевод"\n'
                     'А я буду их сохранять и каждое утро напоминать их повторять!\n'
                     'Если всё понятно, то пишите слова!"', reply_markup=markup)

@bot.message_handler(commands=['back'])
def back_command(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    user.back()
    
    if user.state == 'start':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item3 = types.KeyboardButton("/learn")
        markup.add(item3)
        bot.send_message(chat_id, 'Вы вернулись назад, жми на кнопку "learn" чтобы продолжить изучение слов', 
                         reply_markup=markup)
    elif user.state == 'writing_words':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("/list"), types.KeyboardButton("/ready"), types.KeyboardButton("/back"))
        bot.send_message(chat_id, 'Вы вернулся к добавлению слов. Пишите в формате "слово - перевод".', 
                         reply_markup=markup)
        

@bot.message_handler(commands=['list'])
def show_words(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    user.list()
    
    if user.words:
        bot.send_message(chat_id, f'📖 Ваши слова:\n{user.get_words_list()}')
    else:
        bot.send_message(chat_id, 'У вас пока нет сохранённых слов.')
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/back"), types.KeyboardButton("/ready"), types.KeyboardButton("/clear"))
    bot.send_message(chat_id, 'Вы можете вернуться к добавлению слов, очистить список или перейти в режим обучения.', 
                     reply_markup=markup)

@bot.message_handler(commands=['ready'])
def ready_to_learn(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    user.ready()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/back"))
    
    if user.words:
        bot.send_message(chat_id, 'Вы перешли в режим обучения! Каждое утро в 7:00 я буду присылать вам слова для перевода.\n'
                         'Увидимся завтра!)', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'У вас нет слов для изучения. Добавьте сначала новые слова.', 
                         reply_markup=markup)
        user.continue_learning()

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    if user.state == 'writing_words':
        if '-' in message.text:
            parts = message.text.split('-', 1)
            czech = parts[0].strip()
            translation = parts[1].strip()
            
            if user.add_word(czech, translation):
                bot.send_message(chat_id, f'Слово "{czech}" - "{translation}" сохранено!')
            else:
                bot.send_message(chat_id, f'Это слово "{czech}" - "{translation}" уже добавлено в список!')
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("/list"), types.KeyboardButton("/ready"), types.KeyboardButton("/back"))
            bot.send_message(chat_id, "Что дальше?", reply_markup=markup)
        else:
            bot.send_message(chat_id, 'Неправильный формат! Пример: "děkuji - спасибо"')
    
    elif user.state == 'learning_mode' and user.word_to_check:
        # Проверяем перевод слова
        if user.check_translation(message.text):
            bot.send_message(chat_id, 'Правильно! ✅')
            user.word_to_check = None
            
            if not user.words:
                bot.send_message(chat_id, 'Вы изучили все слова! Можете добавить новые.')
                user.continue_learning()
        else:
            bot.send_message(chat_id, 'Неправильно, попробуйте еще раз.')
            # Возвращаем неправильно переведенное слово в конец списка
            if user.current_word:
                user.words.append(user.current_word)
                user.current_word = None
                user.word_to_check = None

# Запускаем поток для ежедневных напоминаний
threading.Thread(target=schedule_daily_messages, daemon=True).start()

bot.polling(none_stop=True, interval=0)
