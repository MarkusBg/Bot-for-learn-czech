class BaseState:
    def handle(self, bot, message, user, db):
        raise NotImplementedError('handle method must be implemented in subclasses') 