class User:
    def __init__(self, user_id, state=None, last_reminder=None):
        self.user_id = user_id
        self.state = state
        self.last_reminder = last_reminder

class Word:
    def __init__(self, cz_word, ru_word, learned=False):
        self.cz_word = cz_word
        self.ru_word = ru_word
        self.learned = learned 