# -*- coding: utf8 -*-

import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import date, timedelta, datetime
import string

db_name = 'mydb'
password = 'Z0mb%VtCazNLx*4v'
sql_error = 'Įvyko klaida rašant į duomenų bazę.'
token = '618535450:AAGSbVvcmhcKVaEX2ZBbw2aikgTbXgnEmF4'

def day():
    return date.today()

def week():
    return date.today() - timedelta(days=date.today().weekday())

def month():
    return date.today().replace(day=1)

def year():
    return date(year=date.today().year, month=1, day=1)

period = {'d':day,
            'w':week,
            'm':month,
            'y':year}

category = {'mst':'Maistas', 
            'rb':'Rūbai',
            'prmg':'Pramogos',
            'svkt':'Sveikata',
            'sskt':'Sąskaitos',
            'trnsprt':'Transportas',
            'kln':'Kelionės',
            'hgn':'Higiena',
            'kt':'Kita'}

def format(msg):
    updater.bot.send_message(153089796, text=msg, parse_mode='MARKDOWN')

def user(bot, update, args):
    if args[0] == password:
        update.message.reply_text(add_user(update.message.chat.id))
    else:
        update.message.reply_text('Slaptažodis neteisingas.')

def add_user(chat_id):
    db = sqlite3.connect(db_name)
    try:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS
		              users(chat_id INTEGER, UNIQUE(chat_id))''')
        cursor.execute('''INSERT OR IGNORE INTO users(chat_id)
				  VALUES(?)''', (chat_id,))
        db.commit()
        return 'Vartotojas užregistruotas sėkmingai.'
    except Exception as e:
        db.rollback()
        return sql_error
        raise e
    finally:
        db.close()

def msg(bot, update):
    txt = update.message.text.split(None,3)
    if len(txt) < 4:
        reply = 'Įrašo formatas neteisingas.'
    else:
        amt = txt[1]
        exp = txt[2]
        desc = txt[3]
        if txt[0] != 'x':
            reply = 'Naujas įrašas pradedamas _x_ raide.'
        elif len(desc) > 12:
            reply = 'Aprašymas per ilgas.'
        elif not exp in category.keys():
            reply = 'Neteisinga kategorija. Bandykite dar kartą.'
        elif not real(amt):
            reply = 'Įvesta suma nėra skaičius.'
        elif len(amt.split('.')) > 1:
            if len(amt.split('.')[1]) > 2:
                reply = 'Įvesto skaičiaus formatavimas neteisingas.'
            else:
                chat = update.message.chat.id
                dt = str(datetime.today())
                reply = db(chat, amt, exp, desc, dt)   
        else:    
            chat = update.message.chat.id
            dt = str(datetime.today())
            reply = db(chat, amt, exp, desc, dt)
    format(reply)

def real(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def stat(bot, update, args):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    chat_id = update.message.chat.id
    if not args:
        day_since = str(week())
    elif args[0] not in period:
        format('Nurodytas neteisingas laikotarpis')
        return
    else:
        day_since = str(period.get(args[0])())
    try:
        rows = cursor.execute('''SELECT exp, sum(amt) FROM expenses INNER JOIN users ON users.chat_id = expenses.chat WHERE SUBSTR(dt,1,10) >= "''' + day_since + '''" AND chat=? GROUP BY exp''', (chat_id,))
    except:
        rows = 0
    if rows <= 0:
        reply = 'Įrašų nerasta.'
    else:
        s = '```\nIšlaidos nuo ' + day_since + ':```'
        s += '```\n\n'
        result = cursor.fetchall()
        name1 = 'Kategorija'
        name2 = 'Suma, EUR'
        max1 = max(len(max((category.get(i[0]) for i in result), key=len)), len(name1))
        max2 = max(len(max((str(i[1]) for i in result), key=len)), len(name2))

        s += line(max1, max2, 'Kategorija', 'Suma, EUR', ' ')
        s += line(max1, max2, '', '', '-')
        for i in result:
            cat = category.get(i[0])
            s += line(max1, max2, cat, str(i[1]), ' ')
        s += line(max1, max2, '', '', '-')
        s += line(max1, max2, 'Viso', str(sum(i[1] for i in result)), ' ')
        s += '```'

        reply = s.decode('utf8')
    format(reply)

def stat_det(bot, update, args):
    db = sqlite3.connect(db_name)
    cursor = db.cursor()
    chat_id = update.message.chat.id
    if not args:
        day_since = str(week())
    elif args[0] not in period:
        format('Nurodytas neteisingas laikotarpis')
        return
    else:
        day_since = str(period.get(args[0])())
    try:
        rows = cursor.execute('''SELECT SUBSTR(dt,6,5), exp, desc, sum(amt) FROM expenses INNER JOIN users ON users.chat_id = expenses.chat WHERE SUBSTR(dt,1,10) >= "''' + day_since + '''" AND chat=? GROUP BY 1,2,3''', (chat_id,))
    except:
        rows = 0
    if rows <= 0:
        reply = 'Įrašų nerasta.'
    else:
        s = '```\nIšlaidos nuo ' + day_since + ':'
        s += '\n\n'
        result = cursor.fetchall()
        name1 = 'Data'
        name2 = 'Kategorija'
        name3 = 'Aprašymas'
        name4 = 'Suma, EUR'
        max1 = max(len(max((str(i[0]) for i in result), key=len)), len(name1))
        max2 = max(len(max((category.get(i[1]) for i in result), key=len)), len(name2))
        max3 = max(len(max((str(i[2].encode('utf8')) for i in result), key=len)), len(name3.decode('utf8')))
        max4 = max(len(max((str(i[3]) for i in result), key=len)), len(name4))
        

        s += line_det(max1, max2, max3, max4, 'Data', 'Kategorija', 'Aprašymas', 'Suma, EUR', ' ')
        s += line_det(max1, max2, max3, max4, '', '', '', '', '-')
        #print 'keke'
        for i in result:
            cat = category.get(i[1])
            s += line_det(max1, max2, max3, max4, str(i[0]), cat, str(i[2].encode('utf8')), str(i[3]), ' ')
        
        s += line_det(max1, max2, max3, max4, '', '', '', '', '-')
        s += line_det(max1, max2, max3, max4, '', '', 'Viso, EUR', str(sum(i[3] for i in result)), ' ')
        s += '```'

        reply = s.decode('utf8')
    format(reply)

def line(max1, max2, str1, str2, delim):
    return str1 + delim * (max1 - len(str1.decode('utf8')) + 1) + '|' + str2 + delim * (max2 - len(str2) + 1) + '\n'
    
def line_det(max1, max2, max3, max4, str1, str2, str3, str4, delim):
    temp = str1 + delim * (max1 - len(str1) + 1) + '|'
    #temp += str2 + delim * (max2 - len(str2.decode('utf8')) + 1) + '|'
    temp += str3 + delim * (max3 - len(str3.decode('utf8')) + 1) + '|'
    temp += str4 + delim * (max4 - len(str4) + 1) + '\n'
    return temp

def lineg(maxes, strings, delim):
    for i in maxes:
        temp 
    temp = str1 + delim * (max1 - len(str1) + 1) + '|'
    temp += str2 + delim * (max2 - len(str2.decode('utf8')) + 1) + '|'
    temp += str3 + delim * (max3 - len(str3.decode('utf8')) + 1) + '|'
    temp += str4 + delim * (max4 - len(str4) + 1) + '\n'
    return temp

def db(chat, amt, exp, desc, dt):
    #chat_id = update.message.chat.id
    db = sqlite3.connect('mydb')
    try:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS
		              expenses(chat INTEGER, amt REAL, exp TEXT, desc TEXT, dt TEXT, UNIQUE(dt))''')
        cursor.execute('''INSERT OR IGNORE INTO expenses(chat, amt, exp, desc, dt)
				  VALUES(?,?,?,?,?)''', (chat, amt, exp, desc, dt))
        db.commit()
        
        result = cursor.execute('''SELECT sum(amt) FROM expenses INNER JOIN users ON users.chat_id = expenses.chat WHERE SUBSTR(dt,1,10) >= "''' + str(week()) + '''" AND chat=?''', (chat,))
        #print 'nunu'
        return 'Išlaida įrašyta. Šią savaitę jau išleidote ' + str(result.fetchone()[0]) + ' EUR.'
    except Exception as e:
        db.rollback()
        return sql_error
        raise e
    finally:
        db.close()

updater = Updater(token)

#updater.dispatcher.add_handler(CommandHandler('hello', hello))
updater.dispatcher.add_handler(CommandHandler('stat', stat, pass_args = True))
updater.dispatcher.add_handler(CommandHandler('stat_det', stat_det, pass_args = True))
updater.dispatcher.add_handler(MessageHandler(Filters.text, msg))
#updater.dispatcher.add_handler(CommandHandler('start', start, pass_args = True))
updater.dispatcher.add_handler(CommandHandler('user', user, pass_args = True))

updater.start_polling()
updater.idle()
