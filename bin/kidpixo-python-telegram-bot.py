#!/home/mario/.virtualenvs/python-telegram-bot/bin/python3
from telegram.ext import Updater, CommandHandler
import telegram
from telegram.ext import MessageHandler, Filters
import logging
import api_agu as aa

updater = Updater('YOUR_TELEGRAM_BOT_TOKEN') # CHANGE HERE!


def matchtype(i):
    import re
    year = re.compile("^[0-9]+$")
    asterisk = re.compile("^\*$")

    if asterisk.match(i):
        # print('"%s" in the form *' % i)
        return i
    elif year.match(i):
        # print('"%s" in the form YEAR or YR' % i)
        if len(i) is not 4:
            i = '20'+i
        return int(i)
    else:
        # print('No match of known pattern')
        return None


# initialise some data
tokenObj, meetings, meetingsYeartoId = [None]*3

# get the available meetings
# tokenObj = aa.Token(baseurl=aa.baseurl)
# year > id dictionary
meetings = aa.get_data('meetings', aa.tokenObj)
meetingsYeartoId = {int('20'+i['code'][2:]): i['id'] for i in meetings['content']}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(bot, update):
    update.message.reply_text('Hello World!')
# [Code snippets · python-telegram-bot/python-telegram-bot Wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#custom-keyboards)
    custom_keyboard = [[telegram.KeyboardButton(text="/start"), telegram.KeyboardButton(text="/help")]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Custom Keyboard Test",
                     reply_markup=reply_markup)


def hello(bot, update):
    update.message.reply_text(
                            'Hello {}, I am a simple bot to access '
                            '[AGU API](https://api.developer.agu.org:8443/swagger-ui.html).'
                            'Try /help for, well, more help'.format(update.message.from_user.first_name),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="\n".join([
                            "*Commands extended help*",
                            "*/help* - get help on commands",
                            "*/meetings* - get the list of available meetings",
                            "*/dtoken* - (debug) ask for access token and shows it",
                            "*/search* - search in abstracts title in the latest meeting",
                            "*/search* \*YEAR - search in abstracts title in given YEAR",
                            "*/search* \* - search in abstracts title in all meetings",
                            ]), parse_mode=telegram.ParseMode.MARKDOWN)


def getMeetings(bot, update):
    if not aa.tokenObj:
        aa.tokenObj = aa.Token(baseurl=aa.baseurl)
    bot.send_message(chat_id=update.message.chat_id, text='Available Meetings:\n' +
                     '\n'.join(('**title** : {}, **code**: {}, **id**: {}'.format(i['title'], i['code'], i['id']) for i in meetings['content'])),
                     parse_mode=telegram.ParseMode.MARKDOWN)


def token(bot, update):
    if not aa.tokenObj:
        aa.tokenObj = aa.Token(baseurl=aa.baseurl)
    bot.send_message(chat_id=update.message.chat_id, text='Getting token from {}\n'
                     'token last update: {}\n'
                     'token : {}'.format(aa.tokenObj.baseurl, str(aa.tokenObj.lastUpdate), aa.tokenObj.token))


def search(bot, update, args):
    param = {
        'size': 10,  # should come from conf file
        'params': {
            'title': '',
                }
    }

    userYear = matchtype(args[0])
    # out_text = '\n'.join( [str(i)+' - '+e for i,e in zip(range(len(args)),args)] )
    if isinstance(userYear, int):
        meetingIdSearch = meetingsYeartoId.get(userYear)
        titleSearch = ' '.join(args[1:])
        if meetingIdSearch:
            out_text = 'Year: %s, meetinId: %s, search string: "%s"' % (userYear, meetingIdSearch, titleSearch)
            param['params']['meeting.id'] = meetingIdSearch
        else:
            out_text = 'Year: %s, meetinId: %s, search string: "%s"' % (userYear, 'NOT FOUND!', titleSearch)
    elif isinstance(userYear, str):
        out_text = 'Year: all, search string: "%s"' % ' '.join(args[1:])
        titleSearch = '"%s"' % '" AND "'.join(args[1:])
    else:
        param['params']['meeting.id'] = max(meetingsYeartoId.values())
        titleSearch = '"%s"' % '" AND "'.join(args)
        out_text = 'Year: latest id:%s , search string: "%s"' % (param['params']['meeting.id'], titleSearch)

    param['params']['title'] = '"%s"' % titleSearch

    # check if we have a token
    if not aa.tokenObj:
        aa.tokenObj = aa.Token(baseurl=aa.baseurl)
    abstractsSearch = aa.get_data('abstracts/search', aa.tokenObj, parameters=param, debug=True)
    out_text += "\n%s\n" % abstractsSearch.url
    # #TODO: check if no results!
    abstractsSearch = abstractsSearch.json()
    # out_text = out_text + '\nResults Metadata:\n\n' + '\n'.join(['- *{}* : {}'.format(key,val )for key, val in abstractsSearch.items() if key != "content"])
    nresults = len(abstractsSearch)
    out_text += '\nResults %s :\n' % nresults + '\n'.join(['- (%s) %s' % (i['meeting']['title'][0:4], i['title']) for i in abstractsSearch])
    bot.send_message(chat_id=update.message.chat_id, text=out_text, parse_mode=telegram.ParseMode.MARKDOWN)


def unknown(bot, update):
    """Handle unknown commands"""
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


# This handler must be added last
unknown_handler = MessageHandler(Filters.command, unknown)

# add all the Handlers
# TODO: write a function to pass a dict + kwargs that do it automagically
updater.dispatcher.add_handler(CommandHandler('hello', hello))
updater.dispatcher.add_handler(CommandHandler('start', hello))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('meetings', getMeetings))
updater.dispatcher.add_handler(CommandHandler('dtoken', token))
updater.dispatcher.add_handler(CommandHandler('search', search, pass_args=True))
updater.dispatcher.add_handler(unknown_handler)

updater.start_polling()
updater.idle()
