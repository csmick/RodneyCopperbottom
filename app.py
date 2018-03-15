import os, queue
from groupme_bot import Groupme_bot
from flask import Flask, json, request

# timestamped messages queue
timestamped_uids = queue.Queue()


# initialize Flask app
app = Flask(__name__)

# load environment variables
BOT_ID = os.environ['BOT_ID']
GROUP_ID = os.environ['GROUP_ID']
AUTH_TOKEN = os.environ['AUTH_TOKEN']

# instantiate chat bots
groupme_bot = Groupme_bot(BOT_ID, GROUP_ID, AUTH_TOKEN)

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
                groupme_bot.functions[command](args)
        if "@everyone" in message:
            groupme_bot.notify_all(json_body['sender_id'])
        elif "@unmuted" in message:
            groupme_bot.notify_all(json_body['sender_id'], notify_muted=False)

        if timestamped_uids.queue.empty():
            timestamped_uids.queue.put((uid, timestamp))
        else:
            last_uid, last_timestamp = timestamped_uids.queue.get()
            if uid == last_uid:
                timestamped_uids.queue.put((uid, timestamp))
            if timestamped_uids.queue.qsize() >= 3:
                first_timestamp, uid = timestamped_uids.queue.get()
                time = timestamp - first_timestamp
                if time < 30:
                    spammer = json_body['name']
                    groupme_bot.spammer_berate(spammer, uid)
            else:
                timestamped_uids.queue.clear()

    return ''
