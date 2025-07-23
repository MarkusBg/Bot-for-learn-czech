import os

BOT_TOKEN = os.getenv('token')
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'bot.db') 