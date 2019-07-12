# -*- coding: utf-8 -*-
import time
import telebot
import logging
import sys
sys.path.insert(0, './../')
from item import Item
import validators
from database import *

commands = {
	"start": "Registers you to the system",
	"help": "Shows this message",
	"add": "Adds new product to your list",
	"fetch": "Fetch prices of the items in list"
}

class User:

    def __init__(self, user_id, name=''):
        self.id = user_id
        self.user_name = name

        # Item objects

        self.item_list = []

    def add_item(self, url):
        print("Item with url: " + url + " is added")
        item = Item(url)
        item.fetch_soup()
        item.extract_info()
        self.item_list.append(item)

    def check_prices(self):
        updated_items = []
        for item in self.item_list:
            old_price = item.price
            item.update()
            if old_price != item.price:
                updated_items.append(item)
        notify_user(updated_items)

    def get_prices(self):
        result = []
        for item in self.item_list:
            result.append("Price of the item is ₺" + str(int(item.price)))
        return "".join(result)

class Server:

    def __init__(self, bot):
        self.users = {}  # id, User
        self.bot = bot

    def create_user(self, user, name):
        if self.is_registered(user.id):
            return
        new_user = User(user.id, name)
        if new_user not in self.users:
            print ('Creating new user with id', new_user.id)
            self.users[user.id] = new_user
            UserDb.create(id=user.id, name=name)

    def ask_name(self, message):
        name = message.text

    def is_registered(self, user_id):
        try:
            self.users[user_id]
        except KeyError:
            return False
        return True


token = open('token', 'r').read().strip()
bot = telebot.TeleBot(token)
server = Server(bot)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if server.is_registered(message.from_user.id):
        return # TODO
    bot.reply_to(message,
                 "Hello " + message.from_user.first_name)
    bot.send_message(message.chat.id, "You can use /help command to learn how to use this bot")
    server.create_user(user=message.from_user, name=message.text)


@bot.message_handler(commands=['help'])
def command_help(message):
    cid = message.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(commands=['add'])
def add_item(message):
    user = server.users[message.from_user.id]
    url = message.text.replace(" ", "").replace("/add", "")
    if validators.url(url):
        user.add_item(url)
    else:
        bot.reply_to(message, "URL you've provided is wrong, please try again")

@bot.message_handler(commands=['fetch'])
def notify_user(message):
    """ Notify user when price of any item is changed
    """
    user = server.users[message.from_user.id]
    prices = user.get_prices()
    bot.reply_to(message, prices)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if server.is_registered(message.from_user.id) != True:
        bot.reply_to(message, 'Please write /start to register')
    else:
        bot.reply_to(message, "I don't know what you're talking about")
        command_help(message)


while True:
    logging.basicConfig(filename="log",
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)
    try:
        bot.polling(none_stop=True)
    except Exception as err:
        if err == KeyboardInterrupt:
            break
        logging.error(err)
        time.sleep(5)
        print('Internet Error happened')
