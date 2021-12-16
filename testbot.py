import telebot
from telebot import types
from collections import OrderedDict, defaultdict
import requests
import os
from flask import Flask, request


ADRESS, LOCAT, PHOTO = range(3)
USER_STATE = defaultdict(lambda: ADRESS)

def get_state(message):
    return USER_STATE[message.from_user.id]

def update_state(message, state):
    USER_STATE[message.from_user.id] = state


class User:

    location = OrderedDict()

    def __init__(self, user_id):
        self.user_id = user_id


users = list()

commands = {
    "start"    : "Начало использования бота.",
    "add"      : "Добавление нового места.",
    "list"     : "Отображение добавленных мест.",
    "reset"    : "Позволяет пользователю удалить все его добавленные локации.",
    "help"     : "Показать доступные команды.",
}


def open_token(direction):
    with open(direction, "r") as file:
        return file.read()


def check_user(user_id):
    for user in users:
        if user.user_id == user_id:
            return user.location
    else:
        users.append(User(user_id=user_id))


yesornoSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True)
yesornoSelect.add('Да', 'Нет')
hideBoard = types.ReplyKeyboardRemove()

TOKEN = os.getenv("TOKEN", open_token("D:\\Users\\Kokoc\\PycharmProjects\\botcoursera\\token_telegram.txt"))
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://remaindlocationbot.herokuapp.com/{}'.format(TOKEN))
    return "!", 200


@bot.message_handler(commands=["start"])
def start(message):
    check_user(message.from_user.id)
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
    locations = check_user(message.from_user.id)
    if len(locations) == 0:
        bot.send_message(message.from_user.id, "Нет добавленных адресов")
    else:
        for user in users:
            if user.user_id == message.from_user.id:
                for key in user.location:
                    bot.send_message(message.from_user.id, key)
                    bot.send_location(message.from_user.id, user.location[key]["location"][0], user.location[key]["location"][1])
                    bot.send_photo(message.from_user.id, user.location[key]["photo"].content)


@bot.message_handler(commands=["reset"])
def reset_locations(message):
    for user in users:
        if user.user_id == message.from_user.id:
            user.location.clear()
    bot.send_message(message.from_user.id, "I clean yours locations.")


@bot.message_handler(commands=["add"])
def handle_add(message):
    bot.send_message(message.from_user.id, "Введите адрес")
    update_state(message, ADRESS)


@bot.message_handler(func=lambda message: get_state(message) == ADRESS)
def handle_adress(message):
    for user in users:
        if user.user_id == message.from_user.id:
            user.location[message.text] = dict()
            user.location[message.text]['location'] = ""
            user.location[message.text]['photo'] = ""
    bot.send_message(message.from_user.id, "Отправьте локацию")
    update_state(message, LOCAT)


@bot.message_handler(func=lambda message: get_state(message) == LOCAT)
@bot.message_handler(content_types=["location"])
def handle_locat(message):
    for user in users:
        if user.user_id == message.from_user.id:
            for key in user.location:
                if len(user.location[key]["location"]) == 0:
                    user.location[key]["location"] = [message.location.latitude, message.location.longitude]
    bot.send_message(message.from_user.id, "Отправьте фото")
    update_state(message, PHOTO)


@bot.message_handler(func=lambda message: get_state(message) == PHOTO)
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    for user in users:
        if user.user_id == message.from_user.id:
            for key in user.location:
                if user.location[key]["photo"] == "":
                    file_info = bot.get_file(message.photo[-1].file_id)
                    file = requests.get(
                        'https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))
                    user.location[key]["photo"] = file
    bot.send_message(message.from_user.id, "Добавить адрес?", reply_markup=yesornoSelect)
    bot.register_next_step_handler(message, answer_ask)


def answer_ask(message):
    if message.text == "Да":
        bot.send_message(message.from_user.id, "Добавил!")
    elif message.text == "Нет":
        for user in users:
            if user.user_id == message.from_user.id:
                user.location.pop(list(user.location.keys())[-1])


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))