import requests
import datetime 
import json
from scheduler import book_timeslot
import re
import numpy 
from functools import reduce
#create a python file called api_key 
#that contains a dictionary api={"api_key":"your_api_key"}
import api_key
api_key=api_key.api['api_key']
import api


def check_email(email):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if(re.search(regex,email)):  
        print("Valid Email") 
        return True
    else:  
        print("Invalid Email")  
        return False

def getLastMessage(update_id):
    no_response = None, None, None, None, None, None
    result = api.tgGetMessages(update_id)
    size= len(result)
    if (size == 0):
        return no_response
    last_index = size-1
    last_item = result[last_index]

    update_id = last_item['update_id']
    if 'message' not in last_item:
        return no_response
    message = last_item['message']
    message_id = message['message_id']
    chat = message['chat']
    chat_id = chat['id']
    chat_type = chat['type']
    if chat_type != 'group': 
        # print('update not of type group')
        return no_response
    if 'text' not in message:
        return no_response
    last_msg = message['text']
    sender = message['from']
    if sender['is_bot']:
        return no_response
    user_id = sender['id']

    return last_msg,chat_id,update_id, user_id, message_id, sender
    
    # if size < 100:
    #     return last_msg,chat_id,update_id, user_id, message_id
    # else:
    #     print('offseting updates limit...')
    #     url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(api_key,update_id)
    #     response = requests.get(url)
    #     data=response.json()
    #     last_msg=data['result'][len(data['result'])-1]['message']['text']
    #     chat_id=data['result'][len(data['result'])-1]['message']['chat']['id']
    #     update_id=data['result'][len(data['result'])-1]['update_id']
    #     return last_msg,chat_id,update_id


def sendInlineMessageForService(chat_id, reply_to_message_id):
    text='Hi! I am Arc Bot, your corporate scheduling buddy! \n\nYou can control me using these commands\n\n/start-to start chatting with the bot\n/preferred - to see common time intervals\n/vote - to create a poll to vote based on common times\n/schedule [time] - to choose time interval for meeting\n/book - to finalize the booking after emails are sent\n/cancel-to stop chatting with the bot.\n\nFor more information please contact jana.ang@obf.ateneo.edu | celestine.yu@obf.ateneo.edu | john.balaong@obf.ateneo.edu.'
    keyboard={
        'keyboard':
            [
                [{'text':'Progress Report'},{'text':'Post-Project Evaluation'}],
                [{'text':'Planning Seminar'},{'text':'Onboarding'}]
            ],
        'one_time_keyboard': True,
        'selective': True,
    }
    reply_markup=json.JSONEncoder().encode(keyboard)
    response = api.tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text, 
        'reply_markup' : reply_markup, 
        'reply_to_message_id': reply_to_message_id
    })
    return response

time_range = range(8,18)
def generateTimeKeyboard():
    items = []
    current_time=datetime.datetime.now()
    current_hour = current_time.hour
    for hour in time_range:
        #if hour < current_hour:
            #continue
        items.append([{'text': '{0:02}:00'.format(hour)}, {'text': '{0:02}:30'.format(hour)}])
        
    return items

def generateTimeList():
    items = []
    current_time=datetime.datetime.now()
    current_hour = current_time.hour
    for hour in time_range:
        #if hour < current_hour:
            #continue
        items.append('{0:02}:00'.format(hour))
        items.append('{0:02}:30'.format(hour))
    return items

def sendInlineMessageForBookingTime(chat_id):
    text_message='Please choose a time slot...'
    keyboard = generateTimeKeyboard()
    key=json.JSONEncoder().encode({'keyboard': keyboard, 'one_time_keyboard': True})
    response = api.tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text_message, 
        'reply_markup' : key,
    })
    return response

meeting_types = ['Progress Report','Post-Project Evaluation','Planning Seminar','Onboarding']

def book_session(session):
    description = session['description']
    booking_time = session['booking_time']
    emails = session['emails']
    title = session['title']
    response = book_timeslot(description,booking_time,emails, title)
    return response;

def send_common_times (chat_id, times):
    text = 'Here are the common times: {}\n/vote - to create a poll and choose one common time\nPlease type /schedule [time] to finalize your booking schedule'.format(reduce(lambda str, t: str+ '\n- ' + t,times,''))
    # key=json.JSONEncoder().encode({'keyboard': keyboard, 'one_time_keyboard': True})
    response = api.tgSendMessage({ 
        'chat_id': chat_id, 
        'text': text,
        # 'reply_markup' : key,

    })
    return response
    
def cleanup(sessions, chat_id):
    session = sessions.pop(chat_id)
    if session['poll']:
        api.tgStopPoll(chat_id, session['poll'])

def run():
    prev_update_id = None
    sessions = {}
    while True:
        try:
            current_last_msg,chat_id,current_update_id,user_id, message_id, sender =getLastMessage(prev_update_id)
            print(sender)
            sender_username = sender['id'] if sender  else None
            # print({ current_last_msg })
            print(sessions)
            if current_update_id==prev_update_id:
                continue
            
            prev_update_id=current_update_id
            if chat_id in sessions:
                session = sessions[chat_id]
                print(session)
                step = session['step']
                user = session['user']
                
                if (step == 0 and
                    user == user_id and
                    current_last_msg in meeting_types ):
                    time_list = generateTimeList()
                    if (len(time_list) == 0):
                        api.tgSendSimpleReply(chat_id, 'Sorry, no available time slots', message_id)
                        continue;
                    session['step'] = 1
                    session['title'] = current_last_msg

                    sendInlineMessageForBookingTime(chat_id)
                    
                if step == 1:
                    preferred_times = session['preferred_times']
                    if (current_last_msg in generateTimeList()):
                        if sender_username in preferred_times:
                            user_preferred_times = preferred_times[sender_username]
                            if current_last_msg in user_preferred_times:
                                preferred_times[sender_username].remove(current_last_msg)
                            else:
                                preferred_times[sender_username].append(current_last_msg)
                        else:
                            preferred_times[sender_username] = [current_last_msg]
                        
                        continue
                    time_values = preferred_times.values()
                    if (len(time_values) == 0):
                        continue
                    common_times = reduce(numpy.intersect1d, time_values).tolist()
                    if (current_last_msg == '/preferred'):
                        send_common_times(chat_id,common_times)
                        continue
                    if (current_last_msg == '/vote' and user == user_id):
                        if (len(common_times) <= 1):
                            api.tgSendSimpleMessage(chat_id, "nothing to vote on")
                            continue
                        response = api.tgSendPoll(chat_id,'schedule vote', common_times)
                        session['poll'] = response['message_id']
                        continue
                    
                    schedule_match = re.search('^/schedule(?: ([\d]{2}:[\d]{2})|preferred)?', current_last_msg)
                    if (schedule_match and user == user_id):
                        selected_time = schedule_match.group(1)
                        if not selected_time:
                            send_common_times(chat_id,common_times)
                            continue
                        if selected_time == 'preferred':
                            if (len(common_times) ==1):
                                preferred_time = common_times[0]
                                session['booking_time'] = preferred_time
                                session['step'] = 2
                                api.tgSendSimpleMessage(chat_id, "schedule is set to " + preferred_time)
                                api.tgSendSimpleMessage(chat_id,"Please enter email address:\n/book - to finalize the booking once everyone's email addresses have been sent")
                            continue
                        if (selected_time in common_times):
                            session['booking_time'] = selected_time
                            session['step'] = 2
                            api.tgSendSimpleMessage(chat_id, "schedule is set to " + selected_time)
                            api.tgSendSimpleMessage(chat_id,"Please enter email address:")
                        else:
                            api.tgSendSimpleReply(chat_id, "time provided not in your common schedules", message_id)
                            send_common_times(chat_id, common_times)
                descCmd = re.search('^/description (.*)', current_last_msg)  
                if descCmd:
                    session['description'] = descCmd.group(1)
                    api.tgSendSimpleReply(chat_id, "ok", message_id)
                    continue
                if current_last_msg=='/cancel':
                    cleanup(sessions,chat_id)
                    api.tgSendSimpleReply(chat_id, "booking cancelled", message_id)
                    continue
                if (step == 2):
                    if (current_last_msg == '/book'):
                        if len(session['emails']) == 0:
                            api.tgSendSimpleReply(chat_id, "You have not yet sent any email addresses to me yet", message_id)
                            continue
                        response = book_session(sessions[chat_id])
                        if response:
                            api.tgSendSimpleMessage(chat_id,f"Appointment is booked. See you at {session['booking_time']}")
                        else:
                            api.tgSendSimpleMessage(chat_id, "Please try another timeslot and try again tomorrow")
                        cleanup(sessions,chat_id)
                        continue
                    if check_email(current_last_msg):
                        if current_last_msg in sessions[chat_id]['emails']:
                            api.tgSendSimpleReply(chat_id, "That email address is already in the guest list", message_id)
                            continue

                        api.tgSendSimpleReply(chat_id,"Booking please wait.....", message_id)
                        sessions[chat_id]['emails'].append(current_last_msg)
                    else:
                        api.tgSendSimpleReply(chat_id,"Please enter a valid email.\nEnter /cancel to quit chatting with the bot\nThanks!", message_id)

            
            elif current_last_msg=='/start':
                count = api.tgGetChatMembersCount(chat_id)
                sessions[chat_id] = {
                    'step': 0,
                    'user': user_id,
                    'members_count': count,
                    'title': None,
                    'description': None,
                    'booking_time': None,
                    'emails': [],
                    'preferred_times': {},
                    'poll': None,
                }
                print(sessions[chat_id])
                sendInlineMessageForService(chat_id, message_id)
        except:
            continue

            
         
        
            
if __name__ == "__main__":
    run()