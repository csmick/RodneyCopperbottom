#!/usr/bin/python3

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

    def __init__(self, bot_id, group_id, auth_token):
        self.bot_id = bot_id
        self.group_id = group_id
        self.auth_token = auth_token
        self.POST_URL = 'https://api.groupme.com/v3/bots/post'
        self.GROUP_URL = 'https://api.groupme.com/v3/groups/{}'.format(self.group_id)
        self.functions = {'quotes':self.quotes_callback}
        self.quote_service = QuoteService('./data/quotes')
        self.spammer_berates = list()
        with open('./data/spammer_berates.csv') as f:
            for line in f:
                berate = line.strip()
                self.spammer_berates.append(berate)

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, m):
        m.bot_id = self.bot_id
        requests.post(self.POST_URL, json=vars(m))

    def notify_all(self, sender_id, notify_muted=True):
        auth = {'token':self.auth_token}
        members = requests.get(self.GROUP_URL, params=auth).json()['response']['members']
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
        print(berate)
        message_text = '@' + spammer + ' ' + berate 
        message = self.Message(message_text)
        message.mention(uid)
        self.send_message(message)
