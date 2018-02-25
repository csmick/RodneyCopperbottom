import os
from groupme_bot import Groupme_bot
from flask import Flask, json, request

# initialize Flask app
app = Flask(__name__)

# load environment variables
BOT_ID = os.environ['BOT_ID']
GROUP_ID = os.environ['GROUP_ID']

# instantiate chat bots
groupme_bot = Groupme_bot(BOT_ID)

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/groupme', methods=['POST'])
def groupme_callback():
    json_body = request.get_json()
    message = json_body['text']
    if json_body['group_id'] == GROUP_ID and groupme_bot.is_command(message):
        command, args = groupme_bot.parse_message(message)
        groupme_bot.send_message("Command: {}\nArgs: {}".format(command, args));
