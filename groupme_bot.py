#!/usr/bin/python3

import psycopg2
import requests
import shlex
from random import randrange
from quotes import QuoteService

class GroupmeBot(object):

    class Message(object):

        def __init__(self, text=''):
            self.text = text
            self.attachments = []

        def mention(self, uids):
            self.attachments.append({'type':'mentions', 'user_ids':uids})

    def __init__(self, bot_id, group_id, auth_token, database_url):
        self.bot_id = bot_id
        self.group_id = group_id
        self.auth = {'token':auth_token}
        self.database_url = database_url
        self.post_url = 'https://api.groupme.com/v3/bots/post'
        self.group_url = 'https://api.groupme.com/v3/groups/{}'.format(self.group_id)
        self.functions = {'quotes':self.quotes_callback}
        self.quote_service = QuoteService('./data/quotes')
        self.spammer_berates = list()
        with open('./data/spammer_berates.csv') as f:
            for line in f:
                berate = line.strip()
                self.spammer_berates.append(berate)
        self.init_db()

    def init_db(self):
        # connect to database
        conn = psycopg2.connect(self.database_url, sslmode='require')

        # create cursor for database operations
        cur = conn.cursor()

        # create groups table
        cur.execute("CREATE TABLE IF NOT EXISTS groups (group_name varchar, uid varchar, username varchar(64), PRIMARY KEY(group_name, uid));")

        # add 'everyone' group
        members = requests.get(self.group_url, params=self.auth).json()['response']['members']
        for member in members:
            cur.execute('INSERT INTO groups (group_name, uid, username) VALUES (%s, %s, %s) ON CONFLICT (group_name, uid) DO NOTHING;', ('everyone', member['user_id'], member['nickname']))

        # make db changes persistent
        conn.commit()

        # close cursor
        cur.close()

        # close database connection
        conn.close()

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, m):
        m.bot_id = self.bot_id
        requests.post(self.post_url, json=vars(m))

    def notify_all(self, sender_id, notify_muted=True):
        members = requests.get(self.group_url, params=self.auth).json()['response']['members']
        uids = []
        nicknames = []
        for member in members:
            if member['user_id'] != sender_id and (notify_muted or member['muted'] == False):
                uids.append(member['user_id'])
                nicknames.append(member['nickname'])
        message_text = ''
        for nickname in nicknames:
            message_text += ('@' + nickname + ' ')
        message = self.Message(message_text[:-1])
        message.mention(uids)
        self.send_message(message)

    def quotes_callback(self, args):
        topic = args[0] if args else None
        speaker = args[1] if 1 < len(args) else None
        if topic in self.quote_service.list_topics():
            if speaker:
                if speaker not in self.quote_service.list_speakers(topic):
                    message = self.Message('Available speakers: {}'.format(', '.join(map(str, sorted(self.quote_service.list_speakers(topic))))))
                    self.send_message(message)
                    return
            else:
                speakers = self.quote_service.list_speakers(topic)
                speaker_index = randrange(0, len(speakers))
                speaker = speakers[speaker_index]
        else:
            message = self.Message('Available topics: {}'.format(', '.join(map(str, sorted(self.quote_service.list_topics())))))
            self.send_message(message)
            return
        speaker, quote = self.quote_service.get_quote(topic, speaker)
        message = self.Message('{} -{}'.format(quote, speaker))
        self.send_message(message) 
 
    def spammer_berate(self, spammer, uid):
        berate_index = randrange(0, len(self.spammer_berates))
        berate = self.spammer_berates[berate_index]
        message_text = '@' + spammer + ' ' + berate
        message = self.Message(message_text)
        uids = []
        uids.append(uid)
        message.mention(uids)
        self.send_message(message)
