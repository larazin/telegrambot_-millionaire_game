import os
import telebot
import random
import requests

TOKEN = os.getenv('TELETOKEN')
bot = telebot.TeleBot(TOKEN)
API_URL = 'https://stepik.akentev.com/api/millionaire'
button1 = telebot.types.KeyboardButton('1')
button2 = telebot.types.KeyboardButton('2')
button3 = telebot.types.KeyboardButton('3')
button4 = telebot.types.KeyboardButton('4')
button_exit = telebot.types.KeyboardButton('Выйти из игры')
button_start_game = telebot.types.KeyboardButton('Начать игру')
button_score = telebot.types.KeyboardButton('Счет')
button_change_level = telebot.types.KeyboardButton('Смени уровень сложности')
button_show_level = telebot.types.KeyboardButton('Покажи уровень сложности')
main_keyboard = telebot.types.ReplyKeyboardMarkup()
main_keyboard.add(
    button_start_game, button_score, button_change_level, button_show_level
)
change_level_keyboard = telebot.types.ReplyKeyboardMarkup().row(
    button1, button2, button3
)
game_keyboard = telebot.types.ReplyKeyboardMarkup()
game_keyboard.row(
    button1, button2, button3, button4
)
game_keyboard.add(button_exit)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_handler(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    if user_id not in users:
        users[message.from_user.id] = game.copy()  # Добавляется пользователь
        users[user_id]['name'] = name

    if message.text == '/start':
        bot.send_message(user_id, 'Это бот-игра в "Кто хочет стать миллионером', reply_markup=main_keyboard)
    elif message.text.lower() == 'привет':
        bot.send_message(user_id, 'Ну привет!')
    elif message.text in ['Начать игру', '/start_game']:
        exercise(message.from_user.id)
        states[message.from_user.id] = GAME_STATE
    elif message.text in ['Смени уровень сложности', '/change_level']:
        bot.send_message(user_id, 'На какой уровень сложности сменить? От 1 до 3', reply_markup=change_level_keyboard)
        states[message.from_user.id] = LEVEL_STATE
    elif message.text in ['Покажи уровень сложности', '/level']:
        a_level = 'Твой текущий уровень сложности: {}'.format(users[message.from_user.id]['level_id'])
        bot.reply_to(message, a_level)
    elif message.text == 'таблица':
        bot.send_message(user_id, name)
    elif message.text in ['Счет', '/score']:
        score_now = 'Побед: {}; Поражений: {}'.format(users[message.from_user.id]['victories'],
                                                      users[message.from_user.id]['defeats'])
        bot.reply_to(message, score_now)
    else:
        bot.reply_to(message, 'Я тебя не понял')
    print(states)
    print(users)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, GAME_STATE) == GAME_STATE)
def game_handler(message):
    user_id = message.from_user.id
    num_answers = ['1', '2', '3', '4']
    if message.text == str(users[user_id]['answer'] + 1):
        bot.reply_to(message, 'Правильно!')
        users[user_id]['victories'] += 1
        exercise(user_id)
    elif message.text in num_answers and message.text != str(users[user_id]['answer'] + 1):
        bot.reply_to(message, 'Неправильно :(', reply_markup=main_keyboard)
        users[user_id]['defeats'] += 1
        states[user_id] = MAIN_STATE
    elif message.text in 'Выйти из игры':
        bot.reply_to(message, 'Как скажешь', reply_markup=main_keyboard)
        states[user_id] = MAIN_STATE
    else:
        bot.reply_to(message, 'Я тебя не понял')
    print(users)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, LEVEL_STATE) == LEVEL_STATE)
def change_level(message):
    user_id = message.from_user.id
    level = message.text
    try:
        level = int(level)
        if level in range(1, 4):
            users[user_id]['level_id'] = level
            bot.reply_to(message, 'Готово!', reply_markup=main_keyboard)
        else:
            bot.reply_to(message, 'Выйди из бота, разбойник!', reply_markup=main_keyboard)
    except ValueError:
        bot.reply_to(message, 'Выйди из бота, разбойник!', reply_markup=main_keyboard)
    states[user_id] = MAIN_STATE


def exercise(user_id):
    task = requests.get(API_URL, params={'complexity': users[user_id]['level_id']}).json()
    users[user_id]['question'] = task['question']
    answer = task['answers'][0]
    random.shuffle(task['answers'])
    users[user_id]['answer'] = task['answers'].index(answer)
    answers = []
    for index, value in enumerate(task['answers']):
        answers.append('{}) {}'.format(index + 1, value))
    question = '{}\n{}'.format(task['question'], "\n".join(answers))
    bot.send_message(user_id, question, reply_markup=game_keyboard)


if __name__ == '__main__':
    MAIN_STATE = 'main'
    GAME_STATE = 'game_handler'
    LEVEL_STATE = 'change_level_state'
    game = {'victories': 0, 'defeats': 0, 'question': 0, 'answer': 0, 'level_id': 1, 'name': 0}
    users = {}
    states = {}
    bot.polling()
