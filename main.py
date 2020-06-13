from package import vk_parsing_messages
from sys import exit as sys_exit


def start():
    while True:
        answer = input("1 — парсить, 2 — выйти: ")
        if answer == "1":
            vk_parsing_messages.run()
        elif answer == "2":
            sys_exit(0)


if __name__ == "__main__":
    start()
