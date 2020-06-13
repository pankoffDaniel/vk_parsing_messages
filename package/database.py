import sqlite3


class Database:

    def __init__(self, path_db: str, dialogue_id: str,):
        """Инициализация подключения и создание курсора БД"""
        self.dialogue_id = dialogue_id
        self.connection = sqlite3.connect(path_db)
        self.cursor = self.connection.cursor()

    def create_database(self, schema: str):
        """Создание схемы"""
        self.cursor.executescript(schema)

    def get_users(self):
        """Получение всех пользователей"""
        users = self.cursor.execute("SELECT user_name, user_link FROM users").fetchall()
        return users

    def get_dialogue(self):
        """Получение диалога"""
        dialogue = self.cursor.execute("SELECT id, id_dialogue FROM dialogues WHERE id_dialogue = ?", (self.dialogue_id, )).fetchone()
        return dialogue

    def add_users(self, users: set):
        """Добавление пользователей"""
        self.cursor.executemany("INSERT INTO users (user_name, user_link) VALUES (?, ?)", users)

    def add_dialogue(self, datetime: str, spent_time: float):
        """Добавление диалога"""
        self.cursor.execute("INSERT INTO dialogues (utc_datetime_last_parsing, parsing_time, id_dialogue) VALUES  (?, ?, ?)", (datetime, spent_time, self.dialogue_id))

    def update_dialogue(self, datetime: str, spent_time: float):
        """Обновление данных диалога"""
        self.cursor.execute("UPDATE dialogues SET utc_datetime_last_parsing = ?, parsing_time = ? WHERE id_dialogue = ?", (datetime, spent_time, self.dialogue_id))
