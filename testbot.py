import telebot
from telebot import types
from collections import OrderedDict, defaultdict
import requests
import os
from create_db import *
from sqlalchemy.orm import sessionmaker


ADRESS, LOCAT, PHOTO = range(3)
USER_STATE = defaultdict(lambda: ADRESS)

def get_state(message):
    return USER_STATE[message.from_user.id]

def update_state(message, state):
    USER_STATE[message.from_user.id] = state


commands = {
    "start"    : "Начать использовать  бота.",
    "add"      : "Добавление нового места.",
    "list"     : "Отображение добавленных мест.",
    "reset"    : "Удалить все добавленные локации.",
    "help"     : "Показать доступные команды.",
    "delete n"   : "Удалить n-ое место.",
}


Session = sessionmaker(bind = db)
session = Session()

TOKEN = os.environ["TOKEN"]
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    '''
        Получая от пользователя команду /start проверяем, его в БД. Если его нет, то добавляем его по user_id.
    '''
    if len(session.query(User).filter(User.uid == message.from_user.id).all()) > 0:
        pass
    elif len(session.query(User).filter(User.uid == message.from_user.id).all()) == 0:
        user = User(uid=message.from_user.id)
        session.add(user)
        session.commit()
    bot.send_message(message.from_user.id, "Welcome!\nI'm RemainderBot. Let's go!")
    command_help(message)


@bot.message_handler(commands=["help"])
def command_help(message):
    '''
        По команде /help отправляем все доступные команды.
    '''
    help_text = "The following commands are available: \n"
    for key in commands:
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(message.from_user.id, help_text)


@bot.message_handler(commands=["list"])
def show_locations(message):
    '''
        Выводим пользователю все его добавленные локации.
    '''
    if len(session.query(User).filter(User.uid == message.from_user.id).all()) > 1:
        for user in session.query(User).filter(User.uid == message.from_user.id).all():
            answer = "Номер записи - " + str(user.id)
            bot.send_message(message.from_user.id, answer)
            bot.send_message(message.from_user.id, user.adress)
            bot.send_location(message.from_user.id, user.location_latitude, user.location_longitude)
            photo_file = requests.get(user.photo)
            bot.send_photo(message.from_user.id, photo_file.content)
    else:
        user = session.query(User).filter(User.uid == message.from_user.id).one()
        if user.adress == None and user.location_latitude == None \
            and user.location_longitude == None and user.photo == None:
                bot.send_message(message.from_user.id, "Нет добавленных адресов.")
        else:
            answer = "Номер записи - " + str(user.id)
            bot.send_message(message.from_user.id, answer)
            bot.send_message(message.from_user.id, user.adress)
            bot.send_location(message.from_user.id, user.location_latitude, user.location_longitude)
            photo_file = requests.get(user.photo)
            bot.send_photo(message.from_user.id, photo_file.content)


@bot.message_handler(commands=["reset"])
def reset_locations(message):
    '''
        Сбрасываем все лоакции, добавленные пользователем.
    '''
    session.query(User).filter(User.uid == message.from_user.id).delete()
    user = User(uid=message.from_user.id)
    session.add(user)
    session.commit()
    bot.send_message(message.from_user.id, "Я очистил твои локации.")


@bot.message_handler(commands=["delete"])
def delete_locations(message):
    '''
        Удаляем локацию под переданным номером.
    '''
    if "delete" in message.text:
        session.query(User).filter(User.id == int(message.text.split()[1])).delete()
        session.commit()
        bot.send_message(message.from_user.id, "Я удалил данную локацию.")
    else:
        bot.send_message(message.from_user.id, "Нет номера локации.")


@bot.message_handler(commands=["add"])
def handle_add(message):
    '''
        Функция для добавления точки. Проходит с использованием состояний ADRESS, LOCAT, PHOTO для запоминания
        предыдущих ответов.
    '''
    for user in session.query(User).filter(User.uid == message.from_user.id).all():
        if user.adress == None and user.location_latitude == None \
                and user.location_longitude == None and user.photo == None:
            bot.send_message(message.from_user.id, "Введите адрес.")
            update_state(message, ADRESS)
        else:
            user = User(uid=message.from_user.id)
            session.add(user)
            session.commit()
            bot.send_message(message.from_user.id, "Введите адрес.")
            update_state(message, ADRESS)


@bot.message_handler(func=lambda message: get_state(message) == ADRESS)
def handle_adress(message):
    '''
        Получение адреса/кодового слова.
    '''
    for user in session.query(User).filter(User.uid == message.from_user.id).all():
        if user.adress == None:
            user.adress=message.text
            session.add(user)
            session.commit()
    bot.send_message(message.from_user.id, "Отправьте локацию.")
    update_state(message, LOCAT)


@bot.message_handler(func=lambda message: get_state(message) == LOCAT)
@bot.message_handler(content_types=["location"])
def handle_locat(message):
    '''
        Получение локации через функцию телеграмма поделиться геопозицией.:
    '''
    for user in session.query(User).filter(User.uid == message.from_user.id).all():
        if user.location_latitude == None and user.location_longitude == None:
            user.location_latitude = message.location.latitude
            user.location_longitude = message.location.longitude
            session.add(user)
            session.commit()
    bot.send_message(message.from_user.id, "Отправьте фото.")
    update_state(message, PHOTO)


@bot.message_handler(func=lambda message: get_state(message) == PHOTO)
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    '''
        Обработка фотографии.
    '''
    for user in session.query(User).filter(User.uid == message.from_user.id).all():
        if user.photo == None:
            file_info = bot.get_file(message.photo[-1].file_id)
            file = 'https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path)
            user.photo = file
            session.add(user)
            session.commit()
    bot.send_message(message.from_user.id, "Добавил!")


if __name__ == "__main__":
    bot.infinity_polling()