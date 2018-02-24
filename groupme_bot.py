#!/usr/bin/python3

import requests
import shlex

class Groupme_bot(object):

    def __init__(self, bot_id):
        self.bot_id = bot_id

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, m):
        message_data = {
                'bot_id' : self.bot_id,
                'text'   : m,
        }
        requests.post('https://api.groupme.com/v3/bots/post', json=message_data)
