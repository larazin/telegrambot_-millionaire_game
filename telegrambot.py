import os
import telebot
import random
import requests
import json
import redis

TOKEN = os.getenv('TELETOKEN')
REDIS_URL = os.getenv('REDIS_URL')
bot = telebot.TeleBot(TOKEN)
API_URL = 'https://stepik.akentev.com/api/millionaire'

MAIN_STATE = 'main'
GAME_STATE = 'game_handler'
LEVEL_STATE = 'change_level_state'

button1 = telebot.types.KeyboardButton('1')
button2 = telebot.types.KeyboardButton('2')
button3 = telebot.types.KeyboardButton('3')
button4 = telebot.types.KeyboardButton('4')
button_exit = telebot.types.KeyboardButton('Выйти из игры')
button_start_game = telebot.types.KeyboardButton('Начать игру')
button_score = telebot.types.KeyboardButton('Счет')
button_change_level = telebot.types.KeyboardButton('Смени уровень сложности')
button_show_level = telebot.types.KeyboardButton('Покажи уровень сложности')
main_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(
    button_start_game, button_score, button_change_level, button_show_level
)
change_level_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(
    button1, button2, button3
)
game_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
game_keyboard.row(
    button1, button2, button3, button4
)
game_keyboard.add(button_exit)


def redis_save(key, value):
    redis_db = redis.from_url(REDIS_URL)
    value = json.dumps(value)
    redis_db.set(key, value)


def redis_load(key):
    redis_db = redis.from_url(REDIS_URL)
    value = redis_db.get(key)
    if value is None:
        return None
    return json.loads(value)


def get_user_attribute(user_id, attribute):
    user = redis_load(user_id)
    if user is None:
        user = game.copy()  # Добавляется пользователь
        redis_save(user_id, user)
    return user[attribute]


def set_user_attribute(user_id, attribute, new_value):
    user_data = redis_load(user_id)
    user_data[attribute] = new_value
    redis_save(user_id, user_data)


@bot.message_handler(func=lambda message: get_user_attribute(message.from_user.id, 'state') == MAIN_STATE)
def main_handler(message):
    user_id = message.from_user.id

    if message.text == '/start':
        name = message.from_user.first_name
        set_user_attribute(user_id, 'name', name)
        bot.send_message(user_id, 'Это бот-игра в "Кто хочет стать миллионером',
                         reply_markup=main_keyboard)
    elif message.text.lower() == 'привет':
        bot.send_message(user_id, 'Ну привет!')
    elif message.text in ['Начать игру', '/start_game']:
        exercise(message.from_user.id)
        set_user_attribute(user_id, 'state', GAME_STATE)
    elif message.text in ['Смени уровень сложности', '/change_level']:
        bot.reply_to(message, 'На какой уровень сложности сменить? От 1 до 3',
                     reply_markup=change_level_keyboard)
        set_user_attribute(user_id, 'state', LEVEL_STATE)
    elif message.text in ['Покажи уровень сложности', '/level']:
        a_level = 'Твой текущий уровень сложности: {}'.format(get_user_attribute(user_id, 'level_id'))
        bot.reply_to(message, a_level)
    # elif message.text == 'таблица':
    #     bot.send_message(user_id, name)
    elif message.text in ['Счет', '/score']:
        score_now = 'Побед: {}; Поражений: {}'.format(get_user_attribute(user_id, 'victories'),
                                                      get_user_attribute(user_id, 'defeats'))
        bot.send_message(user_id, score_now)
    else:
        bot.reply_to(message, 'Я тебя не понял')


@bot.message_handler(func=lambda message: get_user_attribute(message.from_user.id, 'state') == GAME_STATE)
def game_handler(message):
    user_id = message.from_user.id
    num_answers = ['1', '2', '3', '4']
    answer = str(get_user_attribute(user_id, 'right_answer_index') + 1)
    if message.text == answer:
        bot.reply_to(message, 'Правильно!')
        new_score = get_user_attribute(user_id, 'victories') + 1
        set_user_attribute(user_id, 'victories', new_score)
        exercise(user_id)
    elif message.text in num_answers and message.text != answer:
        bot.reply_to(message, 'Неправильно :(', reply_markup=main_keyboard)
        new_score = get_user_attribute(user_id, 'defeats') + 1
        set_user_attribute(user_id, 'defeats', new_score)
        set_user_attribute(user_id, 'state', MAIN_STATE)
    elif message.text in 'Выйти из игры':
        bot.reply_to(message, 'Как скажешь', reply_markup=main_keyboard)
        set_user_attribute(user_id, 'state', MAIN_STATE)
    else:
        bot.reply_to(message, 'Я тебя не понял')


@bot.message_handler(func=lambda message: get_user_attribute(message.from_user.id, 'state') == LEVEL_STATE)
def change_level(message):
    user_id = message.from_user.id
    level = message.text
    try:
        level = int(level)
        if level in range(1, 4):
            set_user_attribute(user_id, 'level_id', level)
            bot.reply_to(message, 'Готово!', reply_markup=main_keyboard)
        else:
            bot.reply_to(message, 'Выйди из бота, разбойник!', reply_markup=main_keyboard)
    except ValueError:
        bot.reply_to(message, 'Выйди из бота, разбойник!', reply_markup=main_keyboard)
    set_user_attribute(user_id, 'state', MAIN_STATE)


def exercise(user_id):
    task = requests.get(API_URL, params={'complexity': get_user_attribute(user_id, 'level_id')}).json()
    if get_user_attribute(user_id, 'question') != task['question']:
        set_user_attribute(user_id, 'question', task['question'])
        answer = task['answers'][0]
        random.shuffle(task['answers'])
        set_user_attribute(user_id, 'right_answer_index', task['answers'].index(answer))
        answers = []
        for index, value in enumerate(task['answers']):
            answers.append('{}) {}'.format(index + 1, value))
        question = '{}\n{}'.format(task['question'], "\n".join(answers))
        bot.send_message(user_id, question, reply_markup=game_keyboard)
    else:
        exercise(user_id)


if __name__ == '__main__':
    game = {'victories': 0, 'defeats': 0, 'right_answer_index': 0,
            'question': 0, 'level_id': 1, 'name': 0, 'state': MAIN_STATE}
    bot.polling()
