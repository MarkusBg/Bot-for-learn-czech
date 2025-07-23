import re

def validate_word_input(text):
    # Проверка формата: чешское слово и перевод через пробел
    return bool(re.match(r'^\S+\s+\S+$', text.strip()))

def sanitize_input(text):
    # Удаление опасных символов
    return re.sub(r'[;\'"\\]', '', text) 