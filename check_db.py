import sqlite3
import os


def check_existence():
    path = os.getcwd()
    file_list = os.listdir(path)
    if "database.db" not in file_list:
        database = open("database.db", "w")
        connection = sqlite3.connect('database.db')
        c = connection.cursor()
        c.execute("CREATE TABLE dialogues "
                  "(id INTEGER  PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, "
                  "id_dialogue INTEGER  UNIQUE NOT NULL, "
                  "utc_datetime_last_parsing DATETIME NOT NULL,"
                  "parsing_time DOUBLE NOT NULL)")
        c.execute("CREATE TABLE users "
                  "(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, "
                  "user_name TEXT NOT NULL, "
                  "user_link TEXT UNIQUE NOT NULL)")
        database.close()
