#!/usr/bin/python3

import psycopg2
import re
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
        self.conn = psycopg2.connect(self.database_url, sslmode='require')
        self.post_url = 'https://api.groupme.com/v3/bots/post'
        self.group_url = 'https://api.groupme.com/v3/groups/{}'.format(self.group_id)
        self.functions = {'quotes':self.quotes_callback, 'groups':self.subgroups_callback}
        self.quote_service = QuoteService('./data/quotes')
        self.spammer_berates = list()
        with open('./data/spammer_berates.csv') as f:
            for line in f:
                berate = line.strip()
                self.spammer_berates.append(berate)
        self.init_db()
        self.mention_pattern = re.compile('@\w+')

    def init_db(self):
        # create cursor for database operations
        cur = self.conn.cursor()

        # create groups table
        try:
            cur.execute("CREATE TABLE IF NOT EXISTS groups (group_name varchar, uid varchar, username varchar(64), PRIMARY KEY(group_name, uid));")
        except psycopg2.IntegrityError:
            pass

        # add 'everyone' group
        for uid, nickname in self.get_group_members().items():
            cur.execute('INSERT INTO groups (group_name, uid, username) VALUES (%s, %s, %s) ON CONFLICT (group_name, uid) DO NOTHING;', ('everyone', uid, nickname))

        # make db changes persistent
        self.conn.commit()

        # close cursor
        cur.close()

    def is_command(self, m):
        return m.startswith('!')

    def parse_message(self, m):
        m = m[1:]
        l = shlex.split(m)
        return (l[0], l[1:])

    def send_message(self, m):
        m.bot_id = self.bot_id
        requests.post(self.post_url, json=vars(m))

    def get_group_members(self):
        members = {}
        members_list = requests.get(self.group_url, params=self.auth).json()['response']['members']
        for member in members_list:
            members[member['user_id']] = member['nickname']
        return members

    def quotes_callback(self, args, attachments, uid):
        topic = args[0] if args else None
        speaker = args[1] if len(args) > 1 else None
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

    def notify_groups(self, groups):
        cur = self.conn.cursor()
        cur.execute('SELECT uid, username FROM groups WHERE group_name in %s;', (groups,))
        members = set(cur.fetchall())
        uids = []
        nicknames = []
        for member in members:
            uids.append(member[0])
            nicknames.append(member[1])
        message_text = ''
        for nickname in nicknames:
            message_text += ('@' + nickname + ' ')
        message = self.Message(message_text[:-1])
        message.mention(uids)
        self.send_message(message)
        cur.close()

    def subgroups_callback(self, args, attachments, uid):
        action = args[0] if args else None
        if action:

            # create a group
            if action == 'create':
                # parse create arguments
                group_name = args[1] if len(args) > 1 and not args[1].startswith('@') else None

                # ensure group name was specified
                if not group_name:
                    message = self.Message('Please specify a group name.')
                    self.send_message(message)
                    return

                # ensure group doesn't already exist
                if self.subgroup_exists(group_name):
                    message = self.Message('The group "{}" already exists.'.format(group_name))
                    self.send_message(message)
                    return

                # ensure group members were specified
                uids = []
                for a in attachments:
                    if a['type'] == 'mentions':
                        uids = a['user_ids']
                if uids:
                    uids.append(uid)
                    self.create_subgroup(group_name, uids)
                else:
                    message = self.Message('Please specify the members of "{}".'.format(group_name))
                    self.send_message(message)

            # delete a group
            elif action == 'delete':
                # parse delete arguments
                group_name = args[1] if len(args) > 1 else None

                # ensure group name was specified
                if not group_name:
                    message = self.Message('Please specify a group name.')
                    self.send_message(message)
                    return

                # ensure group already exists
                if self.subgroup_exists(group_name):
                    self.delete_subgroup(group_name)
                else:
                    message = self.Message('The group "{}" does not exist.'.format(group_name))
                    self.send_message(message)

            # list existing groups
            elif action == 'list':
                groups = list(self.get_subgroups())
                message = self.Message('Current groups: {}'.format(', '.join(map(str, sorted(groups)))))
                self.send_message(message)

            # list the members of a single group
            elif action == 'members':
                # parse members arguments
                group_name = args[1] if len(args) > 1 else None

                # ensure group name was specified
                if not group_name:
                    message = self.Message('Please specify a group name.')
                    self.send_message(message)
                    return

                # ensure group already exists
                if self.subgroup_exists(group_name):
                    self.list_subgroup_members(group_name)
                else:
                    message = self.Message('The group "{}" does not exist.'.format(group_name))
                    self.send_message(message)
        else:
            message = self.Message('Available actions: create, delete, add, remove, list, members')
            self.send_message(message)

    def get_subgroups(self):
        cur = self.conn.cursor()
        cur.execute('SELECT group_name FROM groups;')
        return set(map(lambda x: x[0], cur.fetchall()))

    def subgroup_exists(self, group_name):
        return group_name in self.get_subgroups()

    def create_subgroup(self, group_name, uids):
        cur = self.conn.cursor()
        members = self.get_group_members()
        for uid in uids:
            cur.execute('INSERT INTO groups (group_name, uid, username) VALUES (%s, %s, %s) ON CONFLICT (group_name, uid) DO NOTHING;', (group_name, uid, members[uid]))
        self.conn.commit()
        message = self.Message('The group "{}" has been created.'.format(group_name))
        self.send_message(message)
        cur.close()

    def delete_subgroup(self, group_name):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM groups WHERE group_name = %s;', (group_name,))
        self.conn.commit()
        message = self.Message('The group "{}" has been deleted.'.format(group_name))
        self.send_message(message)
        cur.close()

    def list_subgroup_members(self, group_name):
        cur = self.conn.cursor()
        cur.execute('SELECT username FROM groups WHERE group_name = %s;', (group_name,))
        members = list(map(lambda x: x[0], cur.fetchall()))
        message = self.Message('Members of "{}": {}'.format(group_name, ', '.join(map(str, sorted(members)))))
        self.send_message(message)
