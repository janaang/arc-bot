from random import Random
import requests
import api_key
import json
import random
from urllib.parse import urlencode
api_key=api_key.api['api_key']

def tgGetJsonResponse(path, params=None):
    if params:
      query = urlencode(params)
      path = '{}?{}'.format(path,query)

    url = "https://api.telegram.org/bot{}/{}".format(api_key, path)
    response = requests.get(url, timeout=60)
    status = response.status_code
    json = response.json()
    if status != 200:
      print('error getting response', json)
    return json

def tgGetUpdates(update_type, offset = None):
  offsetParam = "&offset={}".format(offset) if offset else ""
  return tgGetJsonResponse('getUpdates?allowed_updates={}{}'.format(update_type,offsetParam))['result']

def tgGetMessages(offset = None):
  return tgGetUpdates('message',offset)

def tgGetPolls(offset = None):
  return tgGetUpdates('poll',offset)

def tgSendMessage(params):
  query = urlencode(params)
  path = 'sendMessage?{}'.format(query)
  return tgGetJsonResponse(path)

def tgSendSimpleMessage(chat_id, text):
  return tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text
    })

def tgSendSimpleReply(chat_id, text, message_id):
  return tgSendMessage({ 
        'chat_id': chat_id, 
        'reply_to_message_id': message_id,
        'text': text,
    })

def tgGetChatMembersCount(chat_id):
  return tgGetJsonResponse('getChatMembersCount?chat_id={}'.format(str(chat_id)))['result']

def tgSendPoll(chat_id, question, options):
  query = urlencode({ 
    'chat_id': chat_id, 
    'question': question, 
    'options': json.JSONEncoder().encode(options), 
    'is_anonymous': False,
    'allows_multiple_answers': True,
  })
  path = 'sendPoll?{}'.format(query)
  return tgGetJsonResponse(path)['result']

def tgSendPoll(chat_id, question, options):
  query = urlencode({ 
    'chat_id': chat_id, 
    'question': question, 
    'options': json.JSONEncoder().encode(options), 
    'is_anonymous': False,
    'allows_multiple_answers': True,
  })
  path = 'sendPoll?{}'.format(query)
  return tgGetJsonResponse(path)['result']

def tgStopPoll(chat_id, message_id):
  params= {
    'chat_id': chat_id,
    'message_id': message_id
  }
  return tgGetJsonResponse('stopPoll', params)

if __name__ == "__main__":
    chat_id = -693369611;
    # response = tgSendPoll(-693369611, 'yes?', ['wow',str(random.random())])
    response = tgStopPoll(chat_id, 462)
    print(response)