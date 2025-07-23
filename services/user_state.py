from database.db import Database

def get_user_state(user_id, db: Database):
    return db.get_user_state(user_id)

def set_user_state(user_id, state, db: Database):
    db.set_user_state(user_id, state) 