import os
import telebot
from telebot import types
import pandas as pd
import config
import psycopg2 as psql
import dataframe_image as dfi
from PIL import Image

client = telebot.TeleBot(config.TOKEN)

codes = ['12345']

try:
    connection = psql.connect(
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432",
        database="main_db"
    )
    connection.autocommit = True

    with connection.cursor() as cursor:
        cursor.execute("select * from main_db")
        df = pd.DataFrame(data=cursor)
        df = df.replace(r'\n', ' ', regex=True)

    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'main_db'")
        column_names = pd.DataFrame(data=cursor)
except Exception as _ex:
    print("[INFO] Error with db connection")
finally:
    # noinspection PyUnboundLocalVariable
    if connection:
        # noinspection PyUnboundLocalVariable
        connection.close()
    print("[INFO] Connection with db closed")


@client.message_handler(commands=["start"])
def authentication(message):
    client.send_message(message.chat.id, "Привет!\nЭто интерактивный бот от МАМС! Я помогу вам вывести "
                                         "супермегаинформацию из мегабазы данных!\n\n"
                                         "Для использования бота введите код авторизации ")
    client.register_next_step_handler(message, authorization)


def authorization(message):
    if message.text in codes:
        copy_df = df.copy()
        client.send_message(message.chat.id, "Ваш код принят!\n\nВыберите инструмент, который "
                                             "подходит вам больше всего!")
        buttons_to_choose(message, copy_df)
    else:
        client.send_message(message.chat.id, "Неверный код, попробуйте снова!\n\n")
        authentication(message)


def create_df(message):
    copy_df = df.copy()
    buttons_to_choose(message, copy_df)


def buttons_to_choose(message, copy_df):
    if message.text == 'Нет':
        end_filtration(message, copy_df)
    else:
        buttons = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

        button1 = types.KeyboardButton(text='Домен')
        button2 = types.KeyboardButton(text='Технология')
        button3 = types.KeyboardButton(text='Метод\x20использования')
        button4 = types.KeyboardButton(text='Функциональная\x20группа')
        button5 = types.KeyboardButton(text='Завершить\x20фильтрацию')
        button6 = types.KeyboardButton(text='Начать\20сначала')

        buttons.row(button1, button2)
        buttons.row(button3, button4)
        buttons.row(button5, button6)

        msg = client.send_message(message.chat.id, "Выберите "
                                                   "параметр отбора данных", reply_markup=buttons)
        client.register_next_step_handler(msg, chosen_buttons, copy_df)


def chosen_buttons(message, copy_df):
    chat_id = message.chat.id

    buttons = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button1 = types.KeyboardButton(text='Хорошо!')

    text = "Нажмите на нужный вариант, он скопируется в Ваш буфер, отправьте его обратно!\n\n"

    if message.text == 'Домен':
        msg = client.send_message(chat_id, text, reply_markup=buttons.add(button1))
        client.register_next_step_handler(msg, handler, 2, copy_df)

    if message.text == 'Технология':
        msg = client.send_message(chat_id, text, reply_markup=buttons.add(button1))
        client.register_next_step_handler(msg, handler, 3, copy_df)

    if message.text == 'Метод\x20использования':
        msg = client.send_message(chat_id, text, reply_markup=buttons.add(button1))
        client.register_next_step_handler(msg, handler, 4, copy_df)

    if message.text == 'Функциональная\x20группа':
        msg = client.send_message(chat_id, text, reply_markup=buttons.add(button1))
        client.register_next_step_handler(msg, handler, 5, copy_df)

    if message.text == 'Завершить\x20фильтрацию':
        end_filtration(message, copy_df)

    if message.text == 'Начать\x20сначала':
        create_df(message)


def end_filtration(message, copy_df):
    copy_df.columns = column_names.values
    copy_df = copy_df.drop(copy_df.columns[[6, 8, 10]], axis=1)
    pd.set_option("display.max_column", None)
    pd.set_option("display.max_colwidth", None)
    file_name = "babyFile_" + str(message.chat.id)
    client.send_message(message.chat.id, "Ваш документ формируется, пожалуйста, подождите!")
    client.send_photo(message.chat.id, "https://www.meme-arsenal.com/memes/19285e657beb7bce69bc29b369a194d4.jpg")
    dfi.export(copy_df, f'{file_name}.png', table_conversion="selenium", max_rows=-1, max_cols=-1, fontsize=8, dpi=120)
    image_1 = Image.open(fr'{file_name}.png')
    im_1 = image_1.convert('RGB')
    im_1.save(fr'{file_name}.pdf')
    result_doc = open(f"{file_name}.pdf", "rb")
    client.send_document(message.chat.id, result_doc)
    result_doc.close()
    os.remove(f"{file_name}.pdf")
    os.remove(f"{file_name}.png")

    text1 = "Чтобы начать сначала, нажмите на кнопку или на команду /start!"

    butt = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    butt1 = types.KeyboardButton(text='Начать фильтрацию сначала!')

    msg = client.send_message(message.chat.id, text1, reply_markup=butt.add(butt1))
    client.register_next_step_handler(msg, create_df)


def handler(message, num, copy_df):
    array = copy_df[num].unique()
    print(array)
    res = "Выберите параметр для фильтрации: \n\n"
    for i in range(len(array)):
        res += " \- "
        res += '`' + array[i] + '`'
        res += "\n"
    msg = client.send_message(message.chat.id, text=res, parse_mode='MarkdownV2')
    client.register_next_step_handler(msg, filter_query, num, copy_df)


def filter_query(message, num, copy_df):
    answer = message.text
    if not copy_df[num].eq(answer).any() and answer != '/start':
        text1 = "Такого поля в базе данных не существует. Давайте начнем сначала!"
        butt = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        butt1 = types.KeyboardButton(text='Начать фильтрацию сначала!')
        msg = client.send_message(message.chat.id, text1, reply_markup=butt.add(butt1))
        client.register_next_step_handler(msg, create_df)
    elif answer == '/start':
        authentication(message)
    else:
        copy_df = copy_df.loc[copy_df[num] == answer]
        print(copy_df)
        buttons = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button1 = types.KeyboardButton(text='Да')
        button2 = types.KeyboardButton(text='Нет')
        buttons.add(button1, button2)
        client.send_message(message.chat.id, text="Количество подходящих вариантов на данный момент: "
                                                  + str(len(copy_df.axes[0])))
        msg = client.send_message(message.chat.id, text="Хотите продолжить фильтрацию?", reply_markup=buttons,
                                  parse_mode='MarkdownV2')
        client.register_next_step_handler(msg, buttons_to_choose, copy_df)


client.infinity_polling()

# UNUSED STUFF FOR OTHER TYPE OF OUTPUT

# def row_printer(row_num):
#     result = ""
#     counter = 0
#     for i in range(len(column_names)):
#         # тут проверка на вывод только существующих данных в таблице, убрать из вывода NULL
#         if str(type(df.iloc[row_num][i])) == '<class \'NoneType\'>':
#             continue
#         # тут получаем название колонн строки для вывода
#         result += column_names[0][i]
#         result += ": "
#         result += "\n"
#         # тут получаем остальную инфу для вывода
#         result += str(df.iloc[row_num][i])
#         result += "\n"
#         counter += 1
#     return result
