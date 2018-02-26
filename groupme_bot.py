#!/usr/bin/python3

import requests
import shlex

class Groupme_bot(object):

    def __init__(self, bot_id, group_id, auth_token):
        self.bot_id = bot_id
        self.group_id = group_id
        self.auth_token = auth_token
        self.POST_URL = 'https://api.groupme.com/v3/bots/post'
        self.GROUP_URL = 'https://api.groupme.com/v3/groups/{}'.format(self.group_id)
        self.functions = {}

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, m):
        m['bot_id'] = self.bot_id
        requests.post(self.POST_URL, json=m)

    def notify_all(self):
        auth = {'token':self.auth_token}
        members = requests.get(self.GROUP_URL, params=auth).json()['response']['members']
        uids = map(lambda x: x['user_id'], members)
        print(uids)
        message = {'bot_id':self.bot_id, 'attachments':[{'type':'mentions', 'user_ids':uids}]}
        self.send_message(message)
