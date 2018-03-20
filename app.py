#!/usr/bin/python3

import os
from collections import deque
from groupme_bot import GroupmeBot
from flask import Flask, json, request

# timestamped messages queue
timestamped_uids = deque()

# initialize Flask app
app = Flask(__name__)

# load environment variables
BOT_ID = os.environ['BOT_ID']
GROUP_ID = os.environ['GROUP_ID']
AUTH_TOKEN = os.environ['AUTH_TOKEN']
DATABASE_URL = os.environ['DATABASE_URL']

# instantiate chat bots
groupme_bot = GroupmeBot(BOT_ID, GROUP_ID, AUTH_TOKEN, DATABASE_URL)

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/groupme', methods=['POST'])
def groupme_callback():
    json_body = request.get_json()
    uid = json_body['sender_id']
    timestamp = json_body['created_at']
    message = json_body['text'].replace('“','"').replace('”','"')
    if json_body['group_id'] == GROUP_ID:
        if groupme_bot.is_command(message):
            command, args = groupme_bot.parse_message(message)
            if command in groupme_bot.functions.keys():
                attachments = json_body['attachments'] if 'attachments' in json_body.keys() else []
                groupme_bot.functions[command](args, attachments)

        # check for custom group mentions
        mentions = groupme_bot.mention_pattern.findall(message)
        if(mentions):
            custom_groups = tuple(filter(lambda x: x in groupme_bot.groups, map(lambda x: x[1:], mentions)))
            if(custom_groups):
                groupme_bot.notify_groups(custom_groups)

        if not timestamped_uids:
            timestamped_uids.append((uid, timestamp))
        else:
            first_uid, first_timestamp = timestamped_uids[0]
            if uid == first_uid:
                timestamped_uids.append((uid, timestamp))
                if len(timestamped_uids) >= 3:
                    time = timestamp - first_timestamp
                    if time < 30:
                        spammer = json_body['name']
                        groupme_bot.spammer_berate(spammer, uid)
                        timestamped_uids.clear()
            else:
                timestamped_uids.clear()
                timestamped_uids.append((uid, timestamp))

    return ''
