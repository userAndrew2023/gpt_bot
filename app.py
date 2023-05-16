import enum
import openai
import pymysql as pymysql
import telebot
from mysql.connector import connect
from telebot import types
from config import *

token = TOKEN
bot = telebot.TeleBot(TOKEN)
engine = "text-davinci-003"

users = {}
words = {}
openai.api_key = GPT_API_KEY


class Actions(enum.Enum):
    ACTION_GENERATE = 0
    ACTION_REWRITE = 1


@bot.message_handler(commands=['start'])
def start(message: types.Message):

    con = pymysql.connect(host="localhost", user="root", password="1234", database="back")

    with con.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `bots` WHERE name = '{bot.get_me().username}'")
        id = cursor.fetchall()[0]
        cursor.execute(f"INSERT INTO `messages` (bot_id, username, text) "
                       f"VALUES ('{id[0]}', '{message.from_user.username}', '{message.text}')")
        cursor.execute(f"UPDATE `bots` SET `messages` = '{int(id[3]) + 1}' WHERE (`id` = '{id[0]}');")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = [
        types.KeyboardButton("😎 Аккаунт"),
        types.KeyboardButton("🔮 Генерация текста"),
        types.KeyboardButton("ℹ Инструкция"),
        types.KeyboardButton("✏ Рерайт текста"),
        types.KeyboardButton("📱 Контакты"),
        types.KeyboardButton("🔑 Подписка")
    ]

    markup.add(*items, row_width=2)
    bot.send_message(chat_id=message.chat.id, text="Добро пожаловать в чат-бот 'Dobby.GPT'.  "
                                                   "Я умею создавать красивые тексты и обладаю"
                                                   " способностью перефразировать существующие",
                     reply_markup=markup)

    users[message.chat.id] = None


@bot.message_handler()
def message_handler(message):
    if message.text == "🔮 Генерация текста":
        bot.send_message(message.chat.id, "Введите слова для генерации через пробел")
        users[message.chat.id] = Actions.ACTION_GENERATE
    elif message.text == "✏ Рерайт текста":
        bot.send_message(message.chat.id, "Введите текст", reply_markup=None)
        users[message.chat.id] = Actions.ACTION_REWRITE
    elif message.text == "😎 Аккаунт":
        bot.send_message(message.chat.id, "ID: " + str(message.chat.id))
    elif message.text == "ℹ Инструкция":
        bot.send_message(message.chat.id, """Dobby.GPT

🔥 Инструкция: 
                
😎 Чтобы посмотреть информацию о количестве доступных запросов, нажмите кнопку «Аккаунт»

🔮 Чтобы сгенерировать текст, нажмите кнопку «Генерация текста». 
Введите слова через разделительные символы: 
«пробел»
«enter»
«запятая»
«точка»
«обратный или прямой слэш»

✏️ Чтобы сделать рерайт текста, нажмите кнопку «Рерайт текста». 
Введите текст не более 500 слов.

📱Чтобы просмотреть контактную информацию, нажмите кнопку «Контакты»

🔑 Чтобы посмотреть срок действия подписки нажмите кнопку «Подписка»

По улучшению бота Dobby.GPT пишите на почту info@dobby.plus

Приятного пользования 🫡""")
    elif message.text == "📱 Контакты":
        bot.send_message(message.chat.id, "Техническая поддержка Dobby.GPT:\n+7 800 777-08-35\ninfo@dobby.plus")
    elif message.text == "🔑 Подписка":
        bot.send_message(message.chat.id, "Май: бесплатный период")
    else:
        if users.get(message.chat.id, False) is False:
            bot.send_message(chat_id=message.chat.id, text="Ошибка, попробуйте еще раз")
            users[message.chat.id] = None
        elif users[message.chat.id] == Actions.ACTION_GENERATE:
            if len(message.text.split()) > 100:
                bot.send_message(chat_id=message.chat.id, text="Превышен лимит слов в запросе")
            else:
                bot.send_message(message.chat.id, text="Ваш запрос обрабатывается. Ориентировочное время ответа"
                                                       " до 60 секунд")
                messages = [{"role": "user", "content": f"Сгенерируй текст из слов: {message.text}"}]
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=1000,
                    temperature=1.2,
                    messages=messages
                )
                bot.send_message(chat_id=message.chat.id, text=response["choices"][0]['message']['content'])
                s = open("log.txt", "a")
                s.write(str(message.chat.id) + " - " + message.text + " - " + str(Actions.ACTION_REWRITE) + "\n")
                s.close()

        elif users[message.chat.id] == Actions.ACTION_REWRITE:
            if len(message.text.split()) > 500:
                bot.send_message(chat_id=message.chat.id, text="Превышен лимит слов в запросе")
            else:
                bot.send_message(message.chat.id, text="Ваш запрос обрабатывается. Ориентировочное время ответа"
                                                       " до 60 секунд")
                messages = [{"role": "user", "content": f"Перефразировать текст из слов и заменить синонимами: "
                                                        f"{message.text}"}]
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=1000,
                    temperature=1.2,
                    messages=messages
                )
                bot.send_message(chat_id=message.chat.id, text=response["choices"][0]['message']['content'])
                s = open("log.txt", "a")
                s.write(str(message.chat.id) + " - " + message.text + " - " + str(Actions.ACTION_REWRITE) + "\n")
                s.close()
        else:
            bot.send_message(message.chat.id, "Неверный запрос")


if __name__ == "__main__":
    bot.infinity_polling()
