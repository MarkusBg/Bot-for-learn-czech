import sqlite3
from config import DB_PATH
from datetime import datetime

class Database:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                last_reminder TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                cz_word TEXT,
                ru_word TEXT,
                learned INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                created_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                data TEXT
            )
        ''')
        self.conn.commit()

    def register_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, state) VALUES (?, ?)', (user_id, 'waiting'))
        self.conn.commit()

    def add_word(self, user_id, cz_word, ru_word):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO words (user_id, cz_word, ru_word) VALUES (?, ?, ?)', (user_id, cz_word, ru_word))
        self.conn.commit()

    def get_words(self, user_id, learned=None):
        cursor = self.conn.cursor()
        if learned is None:
            cursor.execute('SELECT id, cz_word, ru_word, learned FROM words WHERE user_id=?', (user_id,))
        else:
            cursor.execute('SELECT id, cz_word, ru_word, learned FROM words WHERE user_id=? AND learned=?', (user_id, learned))
        return cursor.fetchall()

    def set_word_learned(self, word_id, learned=1):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE words SET learned=? WHERE id=?', (learned, word_id))
        self.conn.commit()

    def get_user_state(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT state FROM users WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 'waiting'

    def set_user_state(self, user_id, state):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET state=? WHERE user_id=?', (state, user_id))
        self.conn.commit()

    def save_feedback(self, user_id, message):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO feedback (user_id, message, created_at) VALUES (?, ?, ?)', (user_id, message, datetime.now().isoformat()))
        self.conn.commit()

    def get_reminder_time(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT last_reminder FROM users WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_reminder_time(self, user_id, reminder_time):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET last_reminder=? WHERE user_id=?', (reminder_time, user_id))
        self.conn.commit()

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]

    def delete_word(self, word_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM words WHERE id=?', (word_id,))
        self.conn.commit()

    def close(self):
        self.conn.close() 