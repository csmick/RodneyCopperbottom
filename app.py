import config
from groupme_bot import Groupme_bot
from flask import Flask, json, request

# initialize Flask app
app = Flask(__name__)

# instantiate chat bots
groupme_bot = Groupme_bot(config.bot_id)

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/groupme', methods=['POST'])
def groupme_callback():
    json_body = request.get_json()
    group_id = json_body['group_id']
    message = json_body['text']
    if group_id == config.group_id and groupme_bot.is_command(message):
        command, args = groupme_bot.parse_message(message)
        groupme_bot.send_message("Command: {}\nArgs: {}".format(command, args));
