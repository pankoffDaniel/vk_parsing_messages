from package.database import Database
from collections import OrderedDict
from bs4 import BeautifulSoup
import datetime
import time
import os
import re


def run():
    while True:
        try:
            name_folder = input("ID диалога: ")
            folder_path = os.path.join("messages", name_folder)
            file_list = os.listdir(folder_path)
            # Сортировка "folder_list" по цифрам в названии файла, например, "messages50.html"
            file_list = sorted(file_list, key=lambda number: int(number[8: -5]))
            break
        except OSError:
            print("Неверный путь к папке.")
        except ValueError:
            print("Неверный ввод.")

    # Вспомогательные переменные для работы с файлами и страницами
    len_file_list = len(file_list)
    message_order = None
    start_page = None
    end_page = None
    start = None
    end = None

    # Получаем пользовательский ввод с какой по какую страницу парсить
    while True:
        try:
            print(f"Всего страниц: {len_file_list}")
            start_page = int(input("Первая страница (например — 1): "))
            end_page = int(input(f"Последняя страница (например — {len_file_list}): "))
            print()
        except ValueError:
            print("Неверный ввод.")
            continue

        if start_page > len_file_list or end_page > len_file_list or end_page < 1 or start_page < 1:
            print("Неверное количество.")
            continue
        break

    time_start = time.time()  # Запуска таймера

    # Выбирает в каком виде парсить: по восходящей или по нисходящей, в зависимости от выбранных страниц
    if start_page <= end_page:
        message_order = 1
        start = start_page - 1
        end = end_page
    elif start_page > end_page:
        file_list.reverse()
        message_order = -1
        start = len_file_list - start_page
        end = len_file_list - end_page + 1

    file_name = f"logs_{start_page}-{end_page}.html"  # Название файла для вывода данных

    # Проверка на существование папки "output"
    output_folder = "output"
    current_folder = os.path.join(os.getcwd())
    if output_folder not in os.listdir(current_folder):
        os.mkdir(output_folder)

    # Проверка на существование вложенной папки внутри папки "output"
    if name_folder not in os.listdir(os.path.join(current_folder, output_folder)):
        os.mkdir(os.path.join(current_folder, output_folder, name_folder))

    # log_output = open(f"{os.path.join(output, file_name)}", 'w', encoding='utf-8')
    log_output = open(f"{os.path.join(current_folder, output_folder, name_folder, file_name)}", 'w', encoding='utf-8')

    # Процесс выполнения программы
    progress_percent = 0

    # Список новых пользователей, которых еще нет в БД и они туда попадут
    new_users = []

    # Перебор всех файлов из списка файлов
    for file in file_list[start:end]:
        full_path = os.path.join(folder_path, file)
        with open(full_path, "rb") as opened_file:  # Обязательно rb, так как файлы ВК в ANSI, походу
            raw_html = opened_file.read()
        html = BeautifulSoup(raw_html, "html.parser")
        messages = html.find_all("div", class_="message")

        # Перебор всех сообщений из файла
        for message in messages[::message_order]:
            user_name = message.find("div", class_="message__header").get_text().strip()
            message_date = re.findall(r",\s.*", user_name)[0].strip(', ')
            user_name = re.findall(r".+,", user_name)[0].strip(",")

            # Если сообщение редактировалось, то выводит "(ред.)" в самом конце сообщения
            edited = ""
            if re.findall(r"(ред\.)", message_date):
                message_date = message_date.replace("(ред.)", "").strip()
                edited = "(ред.)"

            # Получение ссылок на профили людей ВК
            # Если ссылки нет, то это собственный профиль, поэтому ссылка на самого себя
            if user_name == "Вы":
                user_href = "https://vk.com/id0"
            else:
                user_href = message.a.get("href")

            # Если текущего пользователя нет в БД, то он добавляется в список, из которого потом все добавятся в БД
            user_data = (user_name, user_href)
            if user_data not in new_users:
                new_users.append(user_data)

            # Получение "грязного" сообщения с html вставками
            user_message = message.div.find_next("div")

            # Действие, связанное с беседой, например: закрепление сообщения, обновление фотографии, исключение и т.д.
            try:
                sub_user_message = message.find("div", class_="kludges")
                dialogue_action = sub_user_message.find("a", class_="im_srv_lnk")
                if dialogue_action:
                    dialogue_action = sub_user_message.get_text().strip()
                    dialogue_action = f"({dialogue_action})"
                else:
                    dialogue_action = ""
            except AttributeError:
                dialogue_action = ""
                sub_user_message = ""

            # Удаление лишних html вставок из сообщения
            user_message = str(user_message)
            user_message = user_message.replace(str(sub_user_message), "")
            user_message = user_message[5:-6]
            user_message = user_message.replace("<br/>", " ")
            user_message = user_message.replace("amp;", "")  # Убирается спец-символ дубликат (для ссылок)

            link_keys = []
            description_values = []
            other_descriptions = []

            attachment_description = message.find_all("div", class_="attachment__description")
            attachment_link = message.find_all("a", class_="attachment__link")
            all_links = []

            for link in attachment_link:
                current_link = f'{link.get("href").strip()}'
                all_links.append(current_link)

            link_types = ["Фотография", "Видеозапись", "Документ", "Ссылка"]

            #  Добавление любого типа сообщения, который не входит в список "link_types"
            if attachment_description:
                for description in attachment_description:
                    current_description = f"{description.get_text().strip()}"
                    if current_description not in link_types:
                        other_descriptions.append(current_description)

            # Документы, голосовые сообщения, видеозаписи и фотографии - полный порядок!
            # Шаблоны для поиска в регулярных выражениях
            pattern_video_url = r"https?://?vk\.com/video\S+"
            pattern_document_url = r"https?://?vk\.com/doc[^s]\S+"
            pattern_audio_message_url = r"https?://?cs[0-9]+\.userapi\.com//?u[0-9]+/audiomsg/.+/.+\.ogg"
            pattern_audio_url = r"https?://?vk\.com/audio\S+"
            pattern_photo_url_1 = r"https?://?sun[0-9]+-[0-9]+\.userapi\.com/\S+\.jpg"
            pattern_photo_url_2 = r"https?://?vk\.com/im\?sel=[0-9]+&z=photo[0-9]+_[0-9]*%[0-9]+Fmail[0-9]+"
            pattern_photo_url_3 = r"https?://?vk\.com/photo\S+"
            pattern_photo_url_4 = r"https?://?pp\.userapi\.com\S+\.jpg"
            pattern_other_url = r"https?://?[^\"\s<>]+"

            # Все найденные ссылки из сообщения
            found_other_urls = re.findall(pattern_other_url, user_message)

            # Не пропускает фотографии по шаблону "pattern_photo_url_4", т.к. они дублируют шаблон "pattern_photo_url_1"
            if found_other_urls and not re.findall(pattern_photo_url_4, user_message):
                for current_url in found_other_urls:
                    all_links.append(current_url)

            url_pattern_types = OrderedDict({
                pattern_document_url: "Документ",
                pattern_audio_message_url: "Голосовое сообщение",
                pattern_photo_url_1: "Фотография",
                pattern_photo_url_2: "Фотография",
                pattern_photo_url_3: "Фотография",
                pattern_photo_url_4: "Фотография",
                pattern_video_url: "Видеозапись",
                pattern_audio_url: "Аудиозапись",
                pattern_other_url: "Ссылка",  # "pattern_other_url" обязательно должен стоять последним!!!
            })

            # Проверяет соответствие типа ссылки с полученной ссылкой и полученным списком типов с шаблонами к ним
            def get_link_and_type(checking_link, url_pattern_type_list):
                for current_pattern, current_type in url_pattern_type_list.items():
                    if re.findall(current_pattern, checking_link) and current_type != "Ссылка":
                        return current_type
                    if current_type == "Ссылка":
                        return False

            for current_link in all_links:
                is_other_url = get_link_and_type(current_link, url_pattern_types)
                if is_other_url:
                    description_values.append(is_other_url)
                else:
                    description_values.append("Ссылка")
                link_keys.append(current_link)

            # Соединение всех ключей-ссылок со значениями-типом ссылки
            attachments = dict(zip(link_keys, description_values))
            # Очистка ключей-ссылок от знаков "#" и "/" в конце ссылки, чтобы оставались только уникальные ссылки
            # Все найденные ссылки удаляются из самого сообщения и переносятся в словарь "ссылка-тип"
            for current_link, current_description in attachments.copy().items():
                if current_link in user_message:
                    user_message = user_message.replace(current_link, "")

                attachments.pop(current_link)
                cleaned_current_link = current_link.rstrip("#").rstrip("/")
                attachments[cleaned_current_link] = current_description

            # Удаляются все совпадения с шаблоном "pattern_photo_url_4" из сообщения
            for current_link in re.findall(pattern_photo_url_4, user_message):
                user_message = user_message.replace(current_link, "")

            # Добавление всех ссылок из сообщения в список справа от спарсенного сообщения
            # Если никаких ссылок нет, то вставляется пустая невидимая строка
            output_links = ""
            if attachments:
                output_links = []
                for current_link in attachments.keys():
                    output_links.append(f'<a href="{current_link}">{current_link}</a>')

            descriptions_and_sum = {}
            descriptions_and_sum_list = []
            output_other_descriptions = []

            if output_links:
                output_links = f"({', '.join(output_links)})"
                attachments_list = list(attachments.values())

                # Подсчет количества уникальных типов ссылок
                for current_description in attachments.values():
                    count_current_description = attachments_list.count(current_description)
                    descriptions_and_sum[current_description] = f"{count_current_description}"

                # Преобразование типа ссылки с добавлением их количества
                for current_description, count_current_description in descriptions_and_sum.items():
                    descriptions_and_sum_list.append(f"({current_description}, {count_current_description} шт.)")

            # Если попался тип "(Аудиозапись)", то проверка, что не повторяется данный тип в "other_descriptions"
            # В ином случае тип сообщения может быть стикером, записью со стены, прикрепленным или удаленным сообщением
            for description in other_descriptions:
                output_description = f"({description}, {other_descriptions.count(description)} шт.)"
                if description == "Аудиозапись" and output_description not in output_other_descriptions:
                    output_other_descriptions.append(output_description)
                elif description != "Аудиозапись":
                    output_other_descriptions.append(f"({description})")

            descriptions_and_sum_list = " ".join(descriptions_and_sum_list)
            output_other_descriptions = " ".join(output_other_descriptions)

            # Удаление рабочих html тэгов, чтобы содержимое не воспринималось как html код
            user_message = user_message.replace("<", "&lt;").replace(">", "&gt;")

            # Добавление одной строчки записи в файл "log_output"
            log_output.writelines(f"<a href='{user_href}'>{user_name}</a> — {dialogue_action}{user_message} {descriptions_and_sum_list} {output_links} {output_other_descriptions} ({message_date}) {edited}</br>")

        progress_percent += 1
        print("Выполнено {0:.2f}%".format(progress_percent / (abs(end_page - start_page) + 1) * 100))

    print(f'\nГотово. Файл "{file_name}" лежит в папке "{os.path.join(output_folder, name_folder)}" рядом с этой программой.\n')
    log_output.close()

    # Остановка таймера, подсчёт времени
    time_end = time.time()
    spent_time = round(time_end - time_start, 2)

    current_datetime = datetime.datetime.utcnow()
    current_datetime = current_datetime.strftime("%d/%m/%y %H:%M:%S")

    name_db = "database.db"
    db_folder = os.path.join(os.getcwd(), "db")
    current_directory_list = os.listdir(db_folder)
    path_db = os.path.join(db_folder, name_db)
    db = Database(path_db, name_folder)

    # Если нет БД, то она создасться в относительном пути
    # Считывается код из схемы и отдается БД на её создание
    if name_db not in current_directory_list:
        schema_path = os.path.join(db_folder, "schema.sql")
        with open(schema_path, 'r') as schema:
            loaded_schema = schema.read()
        db.create_database(loaded_schema)

    # Получение пользователей из БД
    old_users = db.get_users()

    # Добавление всех новых пользователей, которых еще нет в БД
    new_unique_users = set(new_users) - set(old_users)
    db.add_users(new_unique_users)

    # Получение текущего диалога в БД
    dialogue_existence = db.get_dialogue()

    # Если текущий диалог есть в БД, то обноваляется дата и время его последней обработки
    # Если нет, то он добавляется
    if dialogue_existence:
        db.update_dialogue(current_datetime, spent_time)
    elif not dialogue_existence:
        db.add_dialogue(current_datetime, spent_time)

    db.connection.commit()
    db.connection.close()
    print(f"Время выполнения программы в секундах: {spent_time}.\n")
