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
}


yesornoSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)
yesornoSelect.add('Да', 'Нет')
hideBoard = types.ReplyKeyboardRemove()

Session = sessionmaker(bind = db)
session = Session()

TOKEN = os.environ["TOKEN"]
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
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
    help_text = "The following commands are available: \n"
    for key in commands:
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(message.from_user.id, help_text)


@bot.message_handler(commands=["list"])
def show_locations(message):
    if session.query(User).filter(User.uid == message.from_user.id).all():
        for user in session.query(User).filter(User.uid == message.from_user.id).all():
            bot.send_message(message.from_user.id, user.adress)
            bot.send_location(message.from_user.id, user.location_latitude, user.location_longitude)
            bot.send_photo(message.from_user.id, user.photo)
    else:
        bot.send_message(message.from_user.id, "Нет добавленных адресов.")


@bot.message_handler(commands=["reset"])
def reset_locations(message):
    session.query(User).filter(User.uid == message.from_user.id).delete()
    user = User(uid=message.from_user.id)
    session.add(user)
    session.commit()
    bot.send_message(message.from_user.id, "Я очистил твои лоакции.")


@bot.message_handler(commands=["add"])
def handle_add(message):
    bot.send_message(message.from_user.id, "Введите адрес.")
    update_state(message, ADRESS)


@bot.message_handler(func=lambda message: get_state(message) == ADRESS)
def handle_adress(message):
    user = User(uid=message.from_user.id, adress=message.text)
    session.add(user)
    session.commit()
    bot.send_message(message.from_user.id, "Отправьте локацию.")
    update_state(message, LOCAT)


@bot.message_handler(func=lambda message: get_state(message) == LOCAT)
@bot.message_handler(content_types=["location"])
def handle_locat(message):
    for user in session.query(User).filter(User.uid == message.from_user.id).all():
        if (user.location_latitude == None or user.location_latitude == "") and (user.location_longitude == None
                                                                                 or user.location_longitude == ""):
            user.location_latitude = message.location.latitude
            user.location_longitude = message.location.longitude
            session.add(user)
            session.commit()
    bot.send_message(message.from_user.id, "Отправьте фото.")
    update_state(message, PHOTO)


@bot.message_handler(func=lambda message: get_state(message) == PHOTO)
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    for user in session.query(User).filter(User.uid == message.from_user.id).all():
        if user.photo == None or user.location_latitude == "":
            file_info = bot.get_file(message.photo[-1].file_id)
            file = requests.get(
                'https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))
            user.photo = file
            session.add(user)
            session.commit()
    bot.send_message(message.from_user.id, "Добавил!")


if __name__ == "__main__":
    bot.infinity_polling()