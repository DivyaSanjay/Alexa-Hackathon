from __future__ import print_function
import sqlite3, json
from botocore.vendored import requests
from config import *

conn = sqlite3.connect("medic.db")
c = conn.cursor()
speech_output, issues, current_id, gender, year, Problem, last_intent, intent_name = '', '', '', '', '', '', '', ''

def generate_token():
    credentials = username + ':' + hashString
    header = {
        'Authorization': 'Bearer {}'.format(credentials)
    }
    response = requests.post(priaid_authservice_url, headers=header)
    data = json.loads(response.text)
    extraArgs = "token=" + data['Token'] + "&format=json&language=" + language
    return extraArgs

def lambda_handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.0c76d658-3d22-4631-ba5c-e80976b56c41"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])

    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])

    elif event['request']['type'] == "SessionEndedRequest":
        return get_bye_response()

def on_session_started(session_started_request, session):
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    return get_welcome_response()

def on_intent(intent_request, session):
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    global speech_output, issues, current_id, last_intent, intent_name
    session_attributes = {}
    card_title = 'MedicalConditionSearch'
    should_end_session = False
    intent_name = intent_request['intent']['name']

    if intent_name == 'YesIntent':
        if 'about specialists' in speech_output:
            specialists = issues[current_id]['Specialisation']
            if len(specialists) == 0:
                return get_problem_response('I could not find any speicalists for this issue...Can I help you with anything else?')
            data = 'Try'
            vowel = ['a', 'e', 'i', 'o', 'u']
            for i in specialists:
                if i['Name'][0].lower() in vowel:
                    data += ' an '
                else:
                    data += ' a '
                data += i['Name'] + ' or'

            data = data[:-3]
            data += '...Can I help you with anything else?'
            return get_problem_response(data)

        if 'Can I help' in speech_output:
            return get_problem_response('Please specify your symptoms')

        if 'other diagnosis' in speech_output:
            current_id += 1
            return get_problem_response('You might have {}...Do you want to know the treatment option?'.format(issues[current_id]['Issue']['Name']))
        
        query = 'SELECT * FROM issues WHERE ID=' + str(issues[current_id]['Issue']['ID'])
        c.execute(query)
        data = list(c.fetchall())
        return get_issue_response(data[0][2])

    if intent_name == 'NoIntent':
        if 'other diagnosis' in speech_output or 'treatment option' in speech_output:
            return get_problem_response('Do you want to know about specialists for this problem?')
        return get_bye_response()

    if intent_name == 'ByeIntent':
        return get_bye_response()

    if intent_name == 'MedicalConditionSearch' or intent_name == 'DirectTreatment':
        global gender, year, Problem
        slots = intent_request['intent']['slots']
        if slots['Gender'].get('resolutions', None):
            gender = slots['Gender']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
            year = slots['Year']['value']

        if 'Please specify your gender' in speech_output and Problem:
            if gender == '' or year == '':
                return get_problem_response('Please specify your gender and date of birth so that we can provide you accurate diagnosis...for example..say..Male 1997')

            if Problem['resolutionsPerAuthority'][0]['status']['code']=='ER_SUCCESS_NO_MATCH':
                return get_problem_response('I could not find any symptoms matching your problem...Can I help you with anything else?')
            else:
                Problem = Problem['resolutionsPerAuthority'][0]['values'][0]['value']['name']
                extraArgs = generate_token()
                c.execute("SELECT * FROM symptoms WHERE Name='{}'".format(Problem))
                ids = list(c.fetchall())
                ids = [ids[0][0]]
                url = priaid_healthservice_url+'/diagnosis?'+extraArgs+'&symptoms='+json.dumps(ids)+'&gender='+gender+'&year_of_birth='+str(year)
                response = requests.get(url)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    issues = [{'Issue': i['Issue'], 'Specialisation': i['Specialisation']} for i in data]
                    current_id = 0
                else:
                    return get_problem_response('I could not find any issues matching your problem...Can I help you with anything else?')
            
            if last_intent == 'DirectTreatment':
                query = 'SELECT * FROM issues WHERE ID=' + str(issues[current_id]['Issue']['ID'])
                c.execute(query)
                data = list(c.fetchall())
                data = 'You might have {}...'.format(issues[current_id]['Issue']['Name']) + data[0][2]
                return get_issue_response(data)
            
            if issues:
                return get_problem_response('You might have {}...Do you want to know the treatment option?'.format(issues[current_id]['Issue']['Name']))

            return get_problem_response('I could not find any issues matching your problem...Can I help you with anything else?')
        
        Problem = slots['Problem'].get('resolutions', None)
        if Problem:
            if gender == '' or year == '':
                return get_problem_response('Please specify your gender and date of birth so that we can provide you accurate diagnosis...for example..say..Male 1997')

            if Problem['resolutionsPerAuthority'][0]['status']['code']=='ER_SUCCESS_NO_MATCH':
                return get_problem_response('I could not find any symptoms matching your problem...Can I help you with anything else?')
            else:
                Problem = Problem['resolutionsPerAuthority'][0]['values'][0]['value']['name']
                extraArgs = generate_token()
                c.execute("SELECT * FROM symptoms WHERE Name='{}'".format(Problem))
                ids = list(c.fetchall())
                ids = [ids[0][0]]
                url = priaid_healthservice_url+'/diagnosis?'+extraArgs+'&symptoms='+json.dumps(ids)+'&gender='+gender+'&year_of_birth='+str(year)
                response = requests.get(url)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    issues = [{'Issue': i['Issue'], 'Specialisation': i['Specialisation']} for i in data]
                    current_id = 0
                else:
                    return get_problem_response('I could not find any issues matching your problem...Can I help you with anything else?')

            if intent_name == 'DirectTreatment':
                query = 'SELECT * FROM issues WHERE ID=' + str(issues[current_id]['Issue']['ID'])
                c.execute(query)
                data = list(c.fetchall())
                return get_issue_response(data[0][2])

            if issues:
                return get_problem_response('You might have {}...Do you want to know the treatment option?'.format(issues[current_id]['Issue']['Name']))

            return get_problem_response('I could not find any issues matching your problem...Can I help you with anything else?')
        if gender:
            return get_problem_response('Thank You! You are a {} born in {}...You can now tell us your problems.'.format(gender, year))

    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()

    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return get_bye_response()

    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    clear_vars()

def get_issue_response(data):
    global speech_output, issues, intent_name, last_intent
    session_attributes = {}
    card_title = "Treatment"
    if current_id + 1 >= len(issues):
        speech_output = data + "...That's all I have for this problem...Do you want to know about specialists for this problem?"
    else:
        speech_output = data + "...If you don't think this is accurate..I have another diagnosis for you..Do you want to know about it?"
    reprompt_text = speech_output
    should_end_session = False
    last_intent = intent_name
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_problem_response(data):
    global speech_output, intent_name, last_intent
    session_attributes = {}
    card_title = "Treatment"
    speech_output = data 
    reprompt_text = speech_output
    should_end_session = False
    last_intent = intent_name
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_welcome_response():
    global speech_output, intent_name, last_intent
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Medic Bot. Please tell us your gender and year of birth so that we can suggest you accurate treatments..For example..say..Male 1997"
    reprompt_text = speech_output
    should_end_session = False
    last_intent = intent_name
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_help_response():
    global speech_output, intent_name, last_intent
    session_attributes = {}
    card_title = "Help"
    speech_output = "To begin, you can say...I have a cold.. or I have back pain or any other symptoms that you are experiencing"
    reprompt_text = speech_output
    should_end_session = False
    last_intent = intent_name
    return build_response(session_attributes, build_speechlet_response(card_title,speech_output,reprompt_text,should_end_session))

def get_bye_response():
    clear_vars()
    card_title = "Session Ended"
    speech_output = "Thank you for using the Medic Bot! We hope we were helpful."
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def clear_vars():
    global speech_output, issues, current_id, gender, year
    speech_output, issues, current_id, gender, year, last_intent, intent_name = '', '', '', '', '', '', ''
