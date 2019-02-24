import telebot
import os
from requests.exceptions import ConnectionError
from flask import Flask, request
from telebot import types
import requests

token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)
server = Flask(__name__)

selezionata = False
trattaUrbana = False
# tastiera per selezionare tratta urbana o extraurbana
markupTratta = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markupTratta.add('🏢 Urbana', '🏠 Extraurbana')

markupLista = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markupLista.add('❓ Non conosco la lista')

def calcola_tratta_urbana(msg):
    url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/UM/U-{}.pdf'.format(msg.upper())
    r = requests.get(url)
    if r.status_code == 404:
        return "⚠️ La tratta inserita non esiste. Se pensi che sia un errore [contattami](tg://user?id=48837808)"
    return url

def calcola_tratta_extraurbana(msg):
    if len(str(msg)) > 2 and int(msg[0]+msg[1]) > 17:
        url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/ES/{}-{}.pdf'.format(msg[len(msg)-1].upper(),msg[:-1].upper())
    else:
        url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/EN/{}-{}.pdf'.format(msg[len(msg)-1].upper(),msg[:-1].upper())
    r = requests.get(url)
    if r.status_code == 404:
        return "⚠️ La tratta inserita non esiste. Se pensi che sia un errore [contattami](tg://user?id=48837808)"
    return url

@bot.message_handler(commands=['start'])
def select_tratta(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "📍 Inserire linea: ", reply_markup=markupTratta)
@bot.message_handler(func=lambda message: message.text == '🏢 Urbana')
def invia_tratta(message):
    global selezionata
    global trattaUrbana
    selezionata = True
    trattaUrbana = True
    bot.reply_to(message, "🚍 Inserire tratta: (es.12L, 3)", reply_markup = markupLista)


@bot.message_handler(func=lambda message: message.text == '🏠 Extraurbana')
def invia_tratta(message):
    global selezionata
    global trattaUrbana
    selezionata = True
    trattaUrbana = False
    bot.reply_to(message, "🚍 Inserire tratta: (es.6E, 83E)", reply_markup = markupLista)


@bot.message_handler(func=lambda message: message.text == '❓ Non conosco la lista')
def invia_lista(message):
    bot.reply_to(message, "ℹ️ [Qui](https://t.me/lineeactv) puoi trovare la lista con le varie tratte", reply_markup = types.ReplyKeyboardRemove(False), parse_mode="Markdown")



@bot.message_handler(func=lambda message: True)
def echo_all(message):
    global selezionata
    global trattaUrbana

    if selezionata is True:
        if trattaUrbana == True:
            bot.reply_to(message, calcola_tratta_urbana(message.text), parse_mode = 'Markdown')
        else:
            bot.reply_to(message, calcola_tratta_extraurbana(message.text), parse_mode='Markdown')
    else:
        bot.reply_to(message,"Devi prima inserire 🏢 o 🏠")
bot.polling()


@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://telegram-actv-bot.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
