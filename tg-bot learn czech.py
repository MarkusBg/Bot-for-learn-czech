import os
from dotenv import load_dotenv
import telebot
from telebot import types
from transitions import Machine
from datetime import datetime, time
import time as sleep_time
import threading

load_dotenv('.env')
token = os.getenv('token')

bot = telebot.TeleBot(token)

# Словарь для хранения состояний пользователей
user_states = {}

class LearnBot:
    states = ['start', 'writing_words', 'checking_words', 'learning_mode']
    
    transitions = [
        # Переходы из стартового состояния
        {'trigger': 'go', 'source': 'start', 'dest': 'writing_words'},
        {'trigger': 'help', 'source': 'start', 'dest': 'start'},
        {'trigger': 'list', 'source': 'start', 'dest': 'checking_words'},
        
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
        self.current_word_index = 0  # Индекс текущего слова
        self.waiting_for_edit = None  # Ожидание редактирования слова
        
        # Инициализация машины состояний
        self.machine = Machine(model=self, states=LearnBot.states, 
                             transitions=LearnBot.transitions, initial='start')
    
    def add_word(self, czech, translation):
        if (czech, translation) not in self.words:
            self.words.append((czech, translation))
            return True
        return False
    
    def get_words_list(self):
        return '\n'.join([f'{i+1}. {cz} - {tr}' for i, (cz, tr) in enumerate(self.words)])
    
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
    
    def check_translation(self, user_translation):
        """Проверяет правильность перевода"""
        if not self.word_to_check:
            return False
        
        # Приводим к нижнему регистру и убираем лишние пробелы
        correct_translation = self.word_to_check[1].lower().strip()
        user_translation = user_translation.lower().strip()
        
        return correct_translation == user_translation
    
    def get_word_by_index(self, index):
        """Получает слово по индексу"""
        if 0 <= index < len(self.words):
            return self.words[index]
        return None
    
    def remove_word(self, index):
        """Удаляет слово по индексу"""
        if 0 <= index < len(self.words):
            del self.words[index]
            if self.current_word_index >= len(self.words):
                self.current_word_index = 0
            return True
        return False
    
    def edit_word(self, index, new_czech, new_translation):
        """Редактирует слово по индексу"""
        if 0 <= index < len(self.words):
            self.words[index] = (new_czech, new_translation)
            return True
        return False

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
        if user.machine.state == 'learning_mode' and user.words:
            word = user.get_next_word()
            if word:
                user.current_word = word
                user.word_to_check = word
                
                markup = types.InlineKeyboardMarkup()
                show_answer_btn = types.InlineKeyboardButton("Показать ответ", callback_data=f"show_answer_{chat_id}")
                markup.add(show_answer_btn)
                
                bot.send_message(chat_id, f"Повторите слово: {word[0]} - ?", reply_markup=markup)

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

@bot.message_handler(commands=['practice'])
def practice_words(message):
    """Команда для практики слов в любое время"""
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    if not user.words:
        bot.send_message(chat_id, "У вас нет слов для практики. Добавьте сначала новые слова.")
        return
    
    # Сбрасываем состояния перед началом практики
    user.current_word = None
    user.word_to_check = None
    user.current_word_index = 0
    user.waiting_for_edit = None
    
    # Временно переводим в режим обучения
    user.machine.state = 'learning_mode'
    
    word = user.get_next_word()
    if word:
        user.current_word = word
        user.word_to_check = word
        
        markup = types.InlineKeyboardMarkup()
        show_answer_btn = types.InlineKeyboardButton("Показать ответ", callback_data=f"show_answer_{chat_id}")
        markup.add(show_answer_btn)
        
        bot.send_message(chat_id, f"Повторите слово: {word[0]} - ?", reply_markup=markup)

@bot.message_handler(commands=['edit'])
def edit_words(message):
    """Команда для редактирования слов"""
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    if not user.words:
        bot.send_message(chat_id, "У вас нет слов для редактирования.")
        return
    
    user.waiting_for_edit = 'edit'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/back"))
    
    bot.send_message(chat_id, f"📝 Ваши слова для редактирования:\n{user.get_words_list()}\n\n"
                     "Для редактирования напишите номер слова и новый перевод в формате:\n"
                     "номер - новое_чешское_слово - новый_перевод\n"
                     "Например: 1 - děkuji - спасибо", reply_markup=markup)

@bot.message_handler(commands=['delete'])
def delete_words(message):
    """Команда для удаления слов"""
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    if not user.words:
        bot.send_message(chat_id, "У вас нет слов для удаления.")
        return
    
    user.waiting_for_edit = 'delete'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/back"))
    
    bot.send_message(chat_id, f"🗑️ Ваши слова для удаления:\n{user.get_words_list()}\n\n"
                     "Для удаления напишите номер слова.\n"
                     "Например: 1", reply_markup=markup)

@bot.message_handler(commands=['start', 'reset'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    # Полный сброс всех состояний
    user.current_word = None
    user.word_to_check = None
    user.current_word_index = 0
    user.waiting_for_edit = None
    
    user.reset()
    
    bot.send_message(chat_id, 'Привет!')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/help"))
    markup.add(types.KeyboardButton("/learn"), types.KeyboardButton("/practice"))
    markup.add(types.KeyboardButton("/list"), types.KeyboardButton("/edit"), types.KeyboardButton("/delete"))
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
    
    # Сбрасываем состояния перед добавлением слов
    user.current_word = None
    user.word_to_check = None
    user.waiting_for_edit = None
    
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
    
    # Сбрасываем состояния перед переходом
    user.current_word = None
    user.word_to_check = None
    user.waiting_for_edit = None
    
    try:
        user.back()
    except Exception as e:
        # Если переход не удался, просто возвращаемся в стартовое состояние
        user.machine.state = 'start'
    
    if user.machine.state == 'start':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("/help"))
        markup.add(types.KeyboardButton("/learn"), types.KeyboardButton("/practice"))
        markup.add(types.KeyboardButton("/list"), types.KeyboardButton("/edit"), types.KeyboardButton("/delete"))
        bot.send_message(chat_id, 'Вы вернулись в главное меню. Выберите что вам нужно:', reply_markup=markup)
    elif user.machine.state == 'writing_words':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("/list"), types.KeyboardButton("/ready"), types.KeyboardButton("/back"))
        bot.send_message(chat_id, 'Вы вернулись к добавлению слов. Пишите в формате "слово - перевод".', 
                         reply_markup=markup)
    elif user.machine.state == 'checking_words':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("/back"), types.KeyboardButton("/ready"), types.KeyboardButton("/clear"))
        bot.send_message(chat_id, 'Вы можете вернуться к добавлению слов, очистить список или перейти в режим обучения.', 
                         reply_markup=markup)

@bot.message_handler(commands=['list'])
def show_words(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    # Сбрасываем состояния перед переходом
    user.current_word = None
    user.word_to_check = None
    user.waiting_for_edit = None
    
    try:
        user.list()
    except Exception as e:
        # Если переход не удался, просто переходим в состояние checking_words
        user.machine.state = 'checking_words'
    
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
    
    # Сбрасываем состояния перед переходом
    user.current_word = None
    user.word_to_check = None
    user.waiting_for_edit = None
    
    try:
        user.ready()
    except Exception as e:
        # Если переход не удался, просто переходим в состояние learning_mode
        user.machine.state = 'learning_mode'
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/back"))
    
    if user.words:
        bot.send_message(chat_id, 'Вы перешли в режим обучения! Каждое утро в 7:00 я буду присылать вам слова для перевода.\n'
                         'Увидимся завтра!)', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'У вас нет слов для изучения. Добавьте сначала новые слова.', 
                         reply_markup=markup)
        try:
            user.continue_learning()
        except Exception as e:
            user.machine.state = 'writing_words'

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_states:
        user_states[chat_id] = User(chat_id)
    
    user = user_states[chat_id]
    
    if user.machine.state == 'writing_words':
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
    
    elif user.machine.state == 'learning_mode':
        # Проверяем, есть ли слово для проверки
        if user.word_to_check:
            # Проверяем перевод слова
            if user.check_translation(message.text):
                bot.send_message(chat_id, 'Правильно! ✅')
                user.word_to_check = None
                user.current_word = None
                
                # Проверяем, есть ли еще слова для изучения
                if user.words:
                    # Показываем следующее слово
                    word = user.get_next_word()
                    if word:
                        user.current_word = word
                        user.word_to_check = word
                        
                        markup = types.InlineKeyboardMarkup()
                        show_answer_btn = types.InlineKeyboardButton("Показать ответ", callback_data=f"show_answer_{chat_id}")
                        markup.add(show_answer_btn)
                        
                        bot.send_message(chat_id, f"Следующее слово: {word[0]} - ?", reply_markup=markup)
                    else:
                        bot.send_message(chat_id, 'Вы изучили все слова! Можете добавить новые.')
                        user.continue_learning()
                else:
                    bot.send_message(chat_id, 'Вы изучили все слова! Можете добавить новые.')
                    user.continue_learning()
            else:
                bot.send_message(chat_id, 'Неправильно, попробуйте еще раз.')
                # Возвращаем неправильно переведенное слово в конец списка
                if user.current_word:
                    user.words.append(user.current_word)
                    user.current_word = None
                    user.word_to_check = None
        else:
            # Если нет слова для проверки, но мы в режиме обучения, предлагаем начать практику
            bot.send_message(chat_id, 'Используйте команду /practice для начала практики слов.')
    
    # Обработка редактирования слов
    elif user.waiting_for_edit == 'edit':
        if '-' in message.text and message.text.count('-') >= 2:
            parts = message.text.split('-', 2)
            try:
                word_index = int(parts[0].strip()) - 1  # -1 потому что индексы начинаются с 0
                new_czech = parts[1].strip()
                new_translation = parts[2].strip()
                
                if user.edit_word(word_index, new_czech, new_translation):
                    bot.send_message(chat_id, f'Слово успешно отредактировано: "{new_czech}" - "{new_translation}"')
                else:
                    bot.send_message(chat_id, 'Ошибка: неверный номер слова')
            except ValueError:
                bot.send_message(chat_id, 'Ошибка: неверный формат. Пример: 1 - děkuji - спасибо')
        else:
            bot.send_message(chat_id, 'Неправильный формат! Пример: 1 - děkuji - спасибо')
        
        user.waiting_for_edit = None
    
    # Обработка удаления слов
    elif user.waiting_for_edit == 'delete':
        try:
            word_index = int(message.text.strip()) - 1  # -1 потому что индексы начинаются с 0
            word = user.get_word_by_index(word_index)
            if word and user.remove_word(word_index):
                bot.send_message(chat_id, f'Слово "{word[0]}" - "{word[1]}" удалено')
            else:
                bot.send_message(chat_id, 'Ошибка: неверный номер слова')
        except ValueError:
            bot.send_message(chat_id, 'Ошибка: введите номер слова (например: 1)')
        
        user.waiting_for_edit = None

# Запускаем поток для ежедневных напоминаний
threading.Thread(target=schedule_daily_messages, daemon=True).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_answer_'))
def show_answer_callback(call):
    """Обработчик для кнопки 'Показать ответ'"""
    chat_id = int(call.data.split('_')[2])
    
    if chat_id in user_states:
        user = user_states[chat_id]
        if user.word_to_check:
            correct_answer = user.word_to_check[1]
            bot.answer_callback_query(call.id, f"Правильный ответ: {correct_answer}")
            bot.send_message(chat_id, f"Правильный ответ: {correct_answer}")
            
            # Сбрасываем текущее слово
            user.word_to_check = None
            user.current_word = None
            
            # Показываем следующее слово, если есть
            if user.words:
                word = user.get_next_word()
                if word:
                    user.current_word = word
                    user.word_to_check = word
                    
                    markup = types.InlineKeyboardMarkup()
                    show_answer_btn = types.InlineKeyboardButton("Показать ответ", callback_data=f"show_answer_{chat_id}")
                    markup.add(show_answer_btn)
                    
                    bot.send_message(chat_id, f"Следующее слово: {word[0]} - ?", reply_markup=markup)
                else:
                    bot.send_message(chat_id, 'Вы изучили все слова! Можете добавить новые.')
                    user.continue_learning()
            else:
                bot.send_message(chat_id, 'Вы изучили все слова! Можете добавить новые.')
                user.continue_learning()

bot.polling(none_stop=True, interval=0)
