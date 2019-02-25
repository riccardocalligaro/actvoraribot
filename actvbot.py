import telebot, os, re
from requests.exceptions import ConnectionError
from flask import Flask, request
from telebot import types
import requests

class Bus:
    def __init__(self,linea, tratta):
        self.linea = linea
        self.tratta = tratta
    def calcola_tratta(self):
        if self.linea == '🏠 Extraurbana':
            print('devo calcola_trattae')
        if self.linea == '🏢 Urbana':
            pattern = re.compile("([tT]\d)")
            if len(self.tratta)>=2 and pattern.search(self.tratta.replace(" ", "").upper()) is not None:
                url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/UM/U-t_1.pdf'
            else:
                url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/UM/U-{}.pdf'.format(self.tratta.upper())
            r = requests.get(url)
            if r.status_code == 404:
                return "⚠️ La tratta inserita non esiste. Se pensi che sia un errore [contattami](tg://user?id=48837808)"
            return url
        elif self.linea == '🏠 Extraurbana':
            if len(str(self.tratta)) > 2 and int(self.tratta[0]+self.tratta[1]) > 17:
                url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/ES/{}-{}.pdf'.format(self.tratta[len(self.tratta)-1].upper(),self.tratta[:-1].upper())
            else:
                url = 'http://actv.avmspa.it/sites/default/files/attachments/pdf/EN/{}-{}.pdf'.format(self.tratta[len(self.tratta)-1].upper(),self.tratta[:-1].upper())
            r = requests.get(url)
            if r.status_code == 404:
                return "⚠️ La tratta inserita non esiste. Se pensi che sia un errore [contattami](tg://user?id=48837808)"
            return url
        else:
            return "⚠️ Si é verificato un errore"


token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)
server = Flask(__name__)

selezionata = False

# tastiera per selezionare tratta urbana o extraurbana
markupTratta = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markupTratta.add('🏢 Urbana', '🏠 Extraurbana')

#tastiera quando si trova nel campo seleziona tratta
markupLista = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markupLista.add('❓ Non conosco la lista')

@bot.message_handler(commands=['start'])
def select_tratta(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "📍 Inserire linea: ", reply_markup=markupTratta)
@bot.message_handler(func=lambda message: message.text == '🏢 Urbana')
def invia_tratta(message):
    global selezionata
    global linea
    selezionata = True
    linea = '🏢 Urbana'
    bot.reply_to(message, "🚍 Inserire tratta urbana: (es.12L, 3)", reply_markup = markupLista)


@bot.message_handler(func=lambda message: message.text == '🏠 Extraurbana')
def invia_tratta(message):
    global selezionata
    global linea
    selezionata = True
    linea = '🏠 Extraurbana'
    bot.reply_to(message, "🚍 Inserire tratta extraurbana: (es.6E, 83E)", reply_markup = markupLista)

@bot.message_handler(func=lambda message: message.text == '❓ Non conosco la lista')
def invia_lista(message):
    bot.reply_to(message, "ℹ️ [Qui](https://t.me/lineeactv) puoi trovare la lista con le varie tratte", reply_markup = types.ReplyKeyboardRemove(False), parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    global selezionata
    global linea
    if selezionata is True:
        bus = Bus(linea,message.text)
        bot.reply_to(message, "\n📍 Linea: " + linea.upper() + "\n\n🚍 Tratta: "+message.text.upper()+ "\n"+ bus.calcola_tratta(), parse_mode='Markdown')
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
