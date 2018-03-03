#!/usr/bin/python3

import requests
import shlex
from collections import defaultdict
from random import randrange

class Groupme_bot(object):

    class Message(object):

        def __init__(self, text=''):
            self.t = text
            self.attachments = []

        def text(self, text):
            self.t = text
            return self

        def mention(self, uids):
            self.attachments.append({'type':'mentions', 'user_ids':uids})
            return self

        def to_dict(self):
            return {'attachments':self.attachments, 'text':self.t}

    def __init__(self, bot_id, group_id, auth_token):
        self.bot_id = bot_id
        self.group_id = group_id
        self.auth_token = auth_token
        self.POST_URL = 'https://api.groupme.com/v3/bots/post'
        self.GROUP_URL = 'https://api.groupme.com/v3/groups/{}'.format(self.group_id)
        self.functions = {'prequel_quote':self.get_prequel_quote}
        self.prequel_quotes = defaultdict(list)
        with open('./data/prequel_quotes.csv') as f:
            for line in f:
                line = line.strip()
                character, quote = line.split(',', 1)
                self.prequel_quotes[character].append(quote)

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, m):
        m['bot_id'] = self.bot_id
        requests.post(self.POST_URL, json=m)

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
        message = self.Message()
        message.text(message_text[:-1]).mention(uids)
        self.send_message(message.to_dict())

    def get_prequel_quote(self, args):
        character = args[0]
        if character and character not in self.prequel_quotes.keys():
            message = self.Message()
            message.text('No quotes from \"{}\". Here is the list of characters for whom we have quotes:\n    {}'.format(character, '\n    '.join(sorted(self.prequel_quotes.keys()))))
            self.send_message(message.to_dict())
            return
        elif not character:
            characters = list(self.prequel_quotes.keys())
            character_index = randrange(0, len(characters))
            character = characters[character_index]
        quote_index = randrange(0, len(self.prequel_quotes[character]))
        quote = self.prequel_quotes[character][quote_index]
        message = self.Message()
        message.text('{} -{}'.format(quote, character))
        self.send_message(message.to_dict())
