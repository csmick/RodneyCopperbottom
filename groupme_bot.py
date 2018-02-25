#!/usr/bin/python3

import requests
import shlex

class Groupme_bot(object):

    class Message_builder(object):

        def __init__(self):
            self.d = {}
            self.d['attachments'] = []

        def bot_id(self, bot_id):
            self.d['bot_id'] = bot_id

        def text(self, t):
            self.d['text'] = t

        def to_dict(self):
            return self.d

    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, text):
        message = Message_builder().bot_id(self.bot_id).text(text).to_dict()
        requests.post('https://api.groupme.com/v3/bots/post', json=message)
