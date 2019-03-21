import os, sys
from datetime import datetime, timedelta
from flask import Flask, request, abort, jsonify
#import logging
import requests
from ratelimit import limits

#logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

#handler = logging.StreamHandler(sys.stdout)
#handler.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)
#logger.addHandler(handler)

FIVE_MINUTES = 300
WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')
CLIENT_AUTH_TIMEOUT = 24 # in Hours

app = Flask(__name__)

authorised_clients = {}


def tg_say(text):
    BOT_TOKEN=os.getenv('TG_BOT_TOKEN')
    CHAT_ID=os.getenv('TG_CHAT_ID')
    URL = "https://api.telegram.org/bot%s/" % BOT_TOKEN

    api = requests.Session()
    TEXT=text
    response = {'chat_id': CHAT_ID,
                'text' : TEXT
               }
    resp = api.post(URL + "sendMessage", data=response, timeout=1)
    app.logger.info(resp.text)
    return resp.text




def temp_token():
    import binascii
    temp_token = binascii.hexlify(os.urandom(24))
    return temp_token.decode('utf-8')



def handle_err():
  app.logger.info('text'
  tg_say('Get  info: \n {}'.format(text))
  return True


@limits(calls=5, period=FIVE_MINUTES)
@app.route('/webhook_alertmanager', methods=['GET', 'POST'])
def webhook_alertmanager():
    if request.method == 'GET':
        app.logger.info(request.json)
        #app.logger.info(request.headers)
        return '', 200
    elif request.method == 'POST':
        app.logger.info(request.json)
        data = request.json
        for a in data['alerts']:
          app.logger.info(a)
          if a['status'] == 'firing':
              tg_say('{}: {} - {}'.format(a['status'],a['labels']['instance'],a['annotations']['summary']))
        return '', 200
    else:
        abort(400)



@limits(calls=5, period=FIVE_MINUTES)
@app.route('/webhook_grafana', methods=['GET', 'POST'])
def webhook_grafana():
    if request.method == 'GET':
        app.logger.info(request.json)
        #app.logger.info(request.headers)
        return '', 200
    elif request.method == 'POST':
        app.logger.info(request.json)
        data = request.json
        if data['state'] == 'alerting':
          tg_say('{}: {} - {}'.format(data['state'], data['ruleName'], data['message']))
          if data['ruleName'] == '502 err':
            app.logger.info('502 err')
            handle_err()

        return '', 200
    else:
        abort(400)




@limits(calls=5, period=FIVE_MINUTES)
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = request.args.get('verify_token')
        if verify_token == WEBHOOK_VERIFY_TOKEN:
            authorised_clients[request.remote_addr] = datetime.now()
            return jsonify({'status':'success'}), 200
        else:
            return jsonify({'status':'bad token'}), 401

    elif request.method == 'POST':
        client = request.remote_addr
        if client in authorised_clients:
            if datetime.now() - authorised_clients.get(client) > timedelta(hours=CLIENT_AUTH_TIMEOUT):
                authorised_clients.pop(client)
                return jsonify({'status':'authorisation timeout'}), 401
            else:
                print(request.json)
                return jsonify({'status':'success'}), 200
        else:
            return jsonify({'status':'not authorised'}), 401

    else:
        abort(400)

if __name__ == '__main__':
    if WEBHOOK_VERIFY_TOKEN is None:
        print('WEBHOOK_VERIFY_TOKEN has not been set in the environment.\nGenerating random token...')
        token = temp_token()
        print('Token: %s' % token)
        WEBHOOK_VERIFY_TOKEN = token
    app.run('0.0.0.0',port=5000,debug=1)
