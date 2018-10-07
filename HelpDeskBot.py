# -*- coding: utf-8 -*-

from glpi import GLPI
import json
import telebot
from telebot import types
from emoji import emojize

bot_token = 'telegram bot token'
bot = telebot.TeleBot(bot_token)

# list for data, clearing at the end of ticket creating
data = []


# start bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global chatID
    global username
    # find out chat_id
    chatID = message.chat.id
    # find out username
    username = message.from_user.username
    hello_test = 'Добро пожаловать в меню'
    send(hello_test)


# create menu
def send(msg):
    # set buttons row, hide menu after button is pressed
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    # add emojies
    markup.add(emojize(':heavy_plus_sign: Новая заявка', use_aliases=True),
               emojize(':mag_right: Поиск', use_aliases=True))
    # send message from pressed button to the bot
    msg = bot.send_message(chatID, msg, reply_markup=markup)
    bot.register_next_step_handler(msg, process_step)


# handle buttons
def process_step(message):
    if 'Новая заявка' in message.text:
        create(message)
    elif 'Поиск' in message.text:
        search(message)


# input data from user
def create(message):
    bot.send_message(message.chat.id, emojize(":pencil2: Введите тему заявки:", use_aliases=True))
    bot.register_next_step_handler(message, add_theme)


def add_theme(message):
    theme = message.text
    bot.send_message(message.chat.id, emojize(":pencil2: Введите описание проблемы:", use_aliases=True))
    bot.register_next_step_handler(message, add_description)
    data.append(theme)


def add_description(message):
    desc = ('[Отправлено пользователем @{}]\n'.format(username)) + message.text
    data.append(desc)

    # login to GLPI
    url = 'https://hd.integrasky.ru/apirest.php'
    user = 'glpi username'
    password = 'glpi password'
    glpi_token = 'glpi user token'
    glpi = GLPI(url, glpi_token, (user, password))

    # chat_id matching with GLPI organization id (29 is: https://hd.integrasky.ru/front/entity.form.php?id=29)
    def what_group():

        # (тестовый чат)
        if chatID == -200596972:
            return 29

        # ...
        elif chatID == -0:
            return 0

        # ...
        elif chatID == -0:
            return 0

    # send data to glpi
    ticket_payload = {
            'name': data[0].encode('utf-8').decode('latin-1'),
            'content': data[1].encode('utf-8').decode('latin-1'),
            'entities_id': what_group()
            }
    data.clear()

    # message with info, that says the ticket was created
    ticket_dict = glpi.create('ticket', ticket_payload)
    ticket_id = (json.dumps(ticket_dict['id']))
    bot.send_message(message.chat.id,
                     emojize(':white_check_mark: Спасибо! Ваша заявка принята и будет обработана'
                             ' в ближайшее время. Номер заявки: ' + ticket_id, use_aliases=True))
    bot.send_message(message.chat.id,
                     'Введите /start чтобы открыть меню', reply_markup=types.ReplyKeyboardRemove())


# search ticket by ticket_id
def search(message):
    bot.send_message(message.chat.id, emojize(':pencil2: Введите номер заявки:', use_aliases=True))
    bot.register_next_step_handler(message, start_search)


def start_search(message):
    # check ticket_id
    while True:
        try:
            # login to glpi
            ticket_id = int(message.text)
            url = 'https://hd.integrasky.ru/apirest.php'
            user = 'glpi username'
            password = 'glpi password'
            glpi_token = 'glpi user token'
            glpi = GLPI(url, glpi_token, (user, password))

            # search ticket by ticket_id
            search_option = glpi.get('ticket', ticket_id)

            # assign to status codes readable names
            def get_status():
                status_code = search_option.get('status')
                if status_code == 1:
                    return 'Новая'
                elif status_code == 2:
                    return 'В работе (назначена)'
                elif status_code == 3:
                    return 'В работе (запланирована)'
                elif status_code == 4:
                    return 'Ожидает решения'
                elif status_code == 5:
                    return 'Решена'
                elif status_code == 6:
                    return 'Закрыта'

            # parse other data
            ticket_date = search_option.get('date_creation')
            ticket_update = search_option.get('date_mod')
            ticket_name = search_option.get('name')
            ticket_content = search_option.get('content')

            # create message with info about ticket
            ticket_info = 'Информация по заявке\n {}: \n' \
                          'Дата создания:\n {} \n' \
                          'Дата изменения:\n {} \n' \
                          'Статус:\n {} \n' \
                          'Тема:\n {} \n' \
                          'Описание:\n {}'.format(ticket_id, ticket_date, ticket_update, get_status(), ticket_name, ticket_content)
            bot.send_message(message.chat.id, ticket_info)
            bot.send_message(message.chat.id,
                             'Введите /start чтобы открыть меню', reply_markup=types.ReplyKeyboardRemove())

        # if ticket_id is incorrect, show warning message
        except:
            bot.send_message(message.chat.id, emojize(':warning: Заявка c таким номером не найдена', use_aliases=True))
            bot.send_message(message.chat.id,
                             'Введите /start чтобы открыть меню', reply_markup=types.ReplyKeyboardRemove())
        break


bot.polling(none_stop=True)
