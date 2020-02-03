import telebot
import time
import private
import sqlite3

from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# private è un file di tipo .py che conterrà solo la variabile token a cui verrà assegnata la stringa del token fornito da botFather su Telegram
# Esempio di file private.py:
# token = "#"

token = private.token
bot = telebot.TeleBot(token = token, threaded=True, num_threads=5)
# creazione dell'oggetto bot dove viene abilitato il multithread

# Questa classe serve a gestire gli invii di messaggi giornalieri automatici del bot alle chat private e al gruppo telegram
class Automazione(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.mattino = False # Se True significa che è attivo il programma del mattino, cioè invio messaggio di richiesta della presenza o meno in mensa
        self.pranzo = False # Se True significa che è attivo il programma del pranzo , cioè viene inviato il messaggio di riepilogo sul gruppo
        self.sera = True # Se True significa che è attivo il programma del dopo pranzo, cioè vengono settate le disponobilità di tutti i partecipanti a 0

    def run(self):
        while True:
            try:
                if self.mattino == False and self.pranzo == False and self.sera == True and time.strftime("%H:%M") > "07:00" and time.strftime("%H:%M") < "10:00" and time.strftime("%A").lower() != "saturday" and time.strftime("%A").lower() != "sunday":
                    self.sera = False
                    self.mattino = True
                    AvvioMattino()
                elif self.mattino == True and self.pranzo == False and self.sera == False and time.strftime("%H:%M") > "10:20" and time.strftime("%H:%M") < "11:00" and time.strftime("%A").lower() != "saturday" and time.strftime("%A").lower() != "sunday":
                    self.mattino = False
                    self.pranzo = True
                    AvvioPranzo()
                elif self.mattino == False and self.pranzo == True and self.sera == False and time.strftime("%H:%M") > "14:00" and time.strftime("%H:%M") < "15:00" and time.strftime("%A").lower() != "saturday" and time.strftime("%A").lower() != "sunday":
                    self.pranzo = False
                    self.sera = True
                    AvvioSera()
            except:
                print("Errore " + str(self.isAlive()))
            finally:
                time.sleep(600) # Provare ad aumentare i secondi per diminuire l'uso della CPU del server

# Metodo che invia la richiesta automatica mattutina e si collega ai markup della disponibilità
def AvvioMattino():
    connessione = sqlite3.connect("DBMensa.db")
    cursore = connessione.cursor()
    cursore.execute("SELECT IDchat FROM Giornaliero")
    lista_iscritti = cursore.fetchall()
    connessione.close()
    for elem in range(len(lista_iscritti)):
        bot.send_message(lista_iscritti[elem][0], "Buongiorno!!\nCi sei oggi in mensa?", reply_markup=markup_disponibilita())

# Metodo che invia il riepilogo di chi è presente in men
def AvvioPranzo():
    connessione = sqlite3.connect("DBMensa.db")
    cursore = connessione.cursor()
    cursore.execute("SELECT * FROM CodiceGruppo")
    codice = cursore.fetchall()
    if codice != []:
        tabella = createTabella()
        bot.send_message(codice[0][0], "Bella raga! Eccovi il riepilogo giornaliero:\n" + tabella)
    connessione.close()

# Metodo che crea una tabella davvero bella con chi ci sarà o meno in mensa... si la tabella è bellis
def createTabella():
    connessione = sqlite3.connect("DBMensa.db")
    cursore = connessione.cursor()
    cursore.execute("SELECT * FROM Giornaliero")
    lista_iscritti = cursore.fetchall()
    trattini = "----------------------------------------------------------------------------------------------------------------------------------"
    tabella = ""
    if lista_iscritti != []:
        for elem in lista_iscritti:
            # elem[0] = codice chat
            # elem[1] = fascia oraria
            # elem[2] = Nome della persona
            # elem[3] = disponobilità: 1 = si, 0 = no
            tabella += trattini[:int(20-len(elem[2]))] + " " + elem [2] + " " + trattini[:int(20-len(elem[2]))] + "\n"
            if elem[3] != None and int(elem[3]) == 1:
                if(elem[1]) != None:
                    tabella += "È disponibile alle: " + elem[1] + "\n"
                else:
                    tabella += "Che cazzo combini con il bot?\nHai cannato a mettere l'orario\n"
            else:
                tabella += "Non lo vedremo in mensa\n"
    else:
        tabella += "Non ci sono partecipanti da visualizzare"
    connessione.close()
    return tabella

# Metodo che setta tutte le disponobilità a
def AvvioSera():
    connessione = sqlite3.connect("DBMensa.db")
    connessione.execute("UPDATE Giornaliero SET Disponibilita = 0")
    connessione.commit()
    connessione.close()

#Creazione database
def CreateDB():
    connessione = sqlite3.connect("DBMensa.db")
    connessione.execute("CREATE TABLE IF NOT EXISTS 'Giornaliero' ('IDchat' char(50) NOT NULL, 'OrarioPreferito' char(50), 'Nome' char(50), 'Disponibilita' char(1))")
    connessione.execute("CREATE TABLE IF NOT EXISTS 'CodiceGruppo' ('IDchat' char(50))")
    connessione.commit()
    connessione.close()

# Metodo eseguito quando viene eseguito in chat lo /start
@bot.message_handler(commands=['start']) # /start
def start_cmd(message):
    chat_id = message.chat.id
    connessione = sqlite3.connect("DBMensa.db")
    cursore = connessione.cursor()
    if message.chat.type == "group" or message.chat.type == "supergroup":
        # Controllo se il gruppo dalla quale è stato inviato lo start è già all'interno del DB o meno
        cursore.execute("SELECT * FROM CodiceGruppo")
        lista_iscritti = cursore.fetchall()
        flag = False
        for elem in range(len(lista_iscritti)):
            if str(message.chat.id) in lista_iscritti[elem][0]:
                flag = True
                break
        if flag == False:
            bot.reply_to(message, "Ho capito")
            cursore.execute("INSERT INTO CodiceGruppo VALUES (?)", [message.chat.id])
        else:
            bot.reply_to(message, "Non puoi ripetere questa azione")
    else:
        cursore.execute("SELECT IDchat FROM Giornaliero")
        lista_iscritti = cursore.fetchall()
        flag = False
        for elem in range(len(lista_iscritti)):
            if str(chat_id) in lista_iscritti[elem][0]:
                flag = True
        if flag == False:
            connessione = sqlite3.connect("DBMensa.db")
            connessione.execute("INSERT INTO Giornaliero ('IDchat', 'Nome') VALUES (?,?)", [message.chat.id, message.chat.first_name])
        bot.reply_to(message, "Ciao {}".format(message.from_user.first_name))
    connessione.commit()
    connessione.close()

@bot.message_handler(commands=['registrazionegiornaliera'])
def registrazioneManuale(message):
    if message.chat.type == "group" or message.chat.type == "supergroup":
        bot.reply_to(message, "{} non posso, mi dispiace".format(message.from_user.first_name))
    else:
        bot.reply_to(message, "Bene iniziamo a compilare piccole info")
        bot.send_message(message.chat.id, "Ci sei in mensa?", reply_markup=markup_disponibilita())

# Metodi per i comandi inline per la Disponibilita
def markup_disponibilita():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Si", callback_data="risp_si"), InlineKeyboardButton("No", callback_data="risp_no"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    connessione = sqlite3.connect("DBMensa.db")
    cursore = connessione.cursor()
    if call.data == "risp_si":
        bot.answer_callback_query(call.id, "Hai risposto si")
        cursore.execute("UPDATE Giornaliero SET Disponibilita = ? WHERE IDchat = ?", ["1", call.from_user.id])
        bot.send_message(call.from_user.id, "Seleziona la fascia oraria", reply_markup=markup_fasciaOraria())
    elif call.data == "risp_no":
        cursore.execute("UPDATE Giornaliero SET Disponibilita = ? WHERE IDchat = ?", ["0", call.from_user.id])
        bot.answer_callback_query(call.id, "A peccato, sarà per un'altra volta")
        bot.send_message(call.from_user.id, "A peccato, sarà per un'altra volta")
    elif call.data == "12:00 - 12:15":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data == "12:15 - 12:30":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data == "12:30 - 12:45":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data == "12:45 - 13:00":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data == "13:00 - 13:15":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data == "13:15 - 13:30":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data == "13:30 - 13:45":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    elif call.data =="13:45 - 14:00":
        cursore.execute("UPDATE Giornaliero SET OrarioPreferito = ? WHERE IDchat = ?", [call.data, call.from_user.id])
        bot.send_message(call.from_user.id, "Hai scelto la fascia oraria: " + call.data + "\nGrazie per aver inserito tutti i dati, troverai un riepilogo nel gruppo della Mensa... buon appetito!")
    connessione.commit()
    connessione.close()
# Fine comandi inline
# Inizio comandi inline per la scelta della fascia oraria

def markup_fasciaOraria():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("12:00 - 12:15", callback_data="12:00 - 12:15"),
        InlineKeyboardButton("12:15 - 12:30", callback_data="12:15 - 12:30"),
        InlineKeyboardButton("12:30 - 12:45", callback_data="12:30 - 12:45"),
        InlineKeyboardButton("12:45 - 13:00", callback_data="12:45 - 13:00"),
        InlineKeyboardButton("13:00 - 13:15", callback_data="13:00 - 13:15"),
        InlineKeyboardButton("13:15 - 13:30", callback_data="13:15 - 13:30"),
        InlineKeyboardButton("13:30 - 13:45", callback_data="13:30 - 13:45"),
        InlineKeyboardButton("13:45 - 14:00", callback_data="13:45 - 14:00"))
    return markup

@bot.message_handler(commands=['stop'])
def stop(message):
    connessione = sqlite3.connect("DBMensa.db")
    chat_id = message.chat.id
    if message.chat.type == "group" or message.chat.type == "supergroup":
        if message.from_user.id == 415236903:
            bot.send_message(chat_id, "Grazie per avermi utilizzato. Alla prossima :D")
            connessione.execute("DELETE FROM CodiceGruppo WHERE IDchat = ?", [chat_id])
        else:
            bot.send_message(chat_id, "Non mi rimuoverete mai stronzi...")
    else:
        connessione.execute("DELETE FROM Giornaliero WHERE IDchat = ?", [chat_id])
        bot.send_message(chat_id, "Grazie per avermi utilizzato. Alla prossima :D")
    connessione.commit()
    connessione.close()

@bot.message_handler(commands=['riepilogo'])
def riepilogo(message):
    tabella = createTabella()
    bot.send_message(message.chat.id,tabella)

@bot.message_handler(func=lambda message: True)
def Faiqualcosa(message):
    if message.chat.type != "group":
        bot.reply_to(message,"Scusami ma non mi piace chiacchierare :(")

while True:
    try:
        CreateDB()
        try:
            thread_automa = Automazione()
            thread_automa.start()
        except:
            print("Errore con il thread")
        bot.polling()
    except Exception:
        time.sleep(15)
