def get_next_word(user_id, db):
    words = db.get_words(user_id, learned=0)
    if words:
        return words[0]  # (id, cz_word, ru_word, learned)
    return None

def check_answer(user_id, word_id, answer, db):
    words = db.get_words(user_id)
    for w in words:
        if w[0] == word_id:
            if w[2].strip().lower() == answer.strip().lower():
                db.set_word_learned(word_id, 1)
                return True
    return False 