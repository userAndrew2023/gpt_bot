import datetime
import enum
import openai
import psycopg2
import pymysql as pymysql
import telebot
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
    con = connect()
    with con.cursor() as cursor:
        cursor.execute(f"SELECT * FROM users WHERE username = '{message.from_user.username}'")
        f = cursor.fetchall()
        if len(f) == 0:
            cursor.execute(
                f"INSERT INTO users (username, status) VALUES ('{message.from_user.username}', 'active')")
        else:
            if f[0][-1] == "ban":
                bot.send_message(message.chat.id, "Вы были забанены администратором")
                return
        con.commit()
    with con.cursor() as cursor:
        cursor.execute(f"SELECT * FROM bots WHERE name = '{bot.get_me().first_name}'")
        id = cursor.fetchall()[0]
        date = datetime.datetime.now()
        datef = f"{date.day}.{date.month}.{date.year}"
        cursor.execute(f"INSERT INTO messages (bot_id, username, text, datetime) "
                       f"VALUES ('{str(id[0])}', '{message.from_user.username}', '{message.text}', '{datef}')")
        cursor.execute(f"UPDATE bots SET messages = '{str(int(id[3]) + 1)}' WHERE (id = '{str(id[0])}');")
        con.commit()
    con.close()
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


def connect():
    return psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD, host=HOST)


@bot.message_handler()
def message_handler(message):
    con = connect()
    with con.cursor() as cursor:
        cursor.execute(f"SELECT * FROM users WHERE username = '{message.from_user.username}'")
        f = cursor.fetchall()
        if len(f) == 0:
            cursor.execute(
                f"INSERT INTO users (username, status) VALUES ('{message.from_user.username}', 'active')")
        else:
            if f[0][-1] == "ban":
                bot.send_message(message.chat.id, "Вы были забанены администратором")
                return
        con.commit()
    with con.cursor() as cursor:
        cursor.execute(f"SELECT * FROM bots WHERE name = '{bot.get_me().first_name}'")
        id = cursor.fetchall()[0]
        date = datetime.datetime.now()
        datef = f"{date.day}.{date.month}.{date.year}"
        cursor.execute(f"INSERT INTO messages (bot_id, username, text, datetime) "
                       f"VALUES ('{str(id[0])}', '{message.from_user.username}', '{message.text}', '{datef}')")
        cursor.execute(f"UPDATE bots SET messages = '{str(int(id[3]) + 1)}' WHERE (id = '{str(id[0])}');")
        con.commit()
    con.close()

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
                while True:
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            max_tokens=1000,
                            temperature=1.2,
                            messages=messages
                        )
                        break
                    except Exception:
                        pass
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
                while True:
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            max_tokens=1000,
                            temperature=1.2,
                            messages=messages
                        )
                        break
                    except Exception:
                        pass
                bot.send_message(chat_id=message.chat.id, text=response["choices"][0]['message']['content'])
                s = open("log.txt", "a")
                s.write(str(message.chat.id) + " - " + message.text + " - " + str(Actions.ACTION_REWRITE) + "\n")
                s.close()
        else:
            bot.send_message(message.chat.id, "Неверный запрос")


if __name__ == "__main__":
    con = connect()
    bot.infinity_polling()
