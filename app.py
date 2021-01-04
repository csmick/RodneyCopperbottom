#!/usr/bin/python3

"""Flask application."""

import os

from database.database_container import DatabaseContainer
from groupme_bot import GroupmeBot
from flask import Flask, request

# initialize Flask app
app = Flask(__name__)

# load environment variables
BOT_ID = os.environ['BOT_ID']
GROUP_ID = os.environ['GROUP_ID']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

# configure the database client
database_container = DatabaseContainer()
database_container.config.database_url.from_env('DATABASE_URL')
database_container.config.sslmode = 'require'
database_container.config.minconn = 1
database_container.config.maxconn = 5

# instantiate chat bots
groupme_bot = GroupmeBot(BOT_ID, GROUP_ID, AUTH_TOKEN)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/groupme', methods=['POST'])
def groupme_callback():
    json_body = request.get_json()
    uid = json_body['sender_id']
    message = json_body['text'].replace('“','"').replace('”','"')
    if json_body['group_id'] == GROUP_ID:
        if groupme_bot.is_command(message):
            command, args = groupme_bot.parse_message(message)
            if command in groupme_bot.functions.keys():
                attachments = []
                if 'attachments' in json_body.keys():
                    attachments = json_body['attachments']
                groupme_bot.functions[command](args, attachments, uid)

        # check for custom group mentions
        mentions = groupme_bot.mention_pattern.findall(message)
        if mentions:
            database_client = database_container.client()
            custom_groups = tuple(
                filter(lambda x: x in database_client.get_subgroups(),
                map(lambda x: x[1:], mentions)))
            if custom_groups:
                groupme_bot.notify_groups(custom_groups)

    return ''
