from __future__ import print_function
from logic import *

def lambda_handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.173ea919-b9c1-4f06-92ad-81968280cbb7"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])

    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])

    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

def on_session_started(session_started_request, session):
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    return get_welcome_response()

def on_intent(intent_request, session):
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    session_attributes = {}
    card_title = 'Restaurant_Search'
    should_end_session = False
    intent_name = intent_request['intent']['name']

    if intent_name == "HelloIntent":
        speech_output = get_bot_response('greet', [])
        reprompt_text = speech_output
        return build_response(session_attributes, 
                            build_speechlet_response(card_title,speech_output,reprompt_text,should_end_session))

    elif intent_name == "ByeIntent":
        speech_output = get_bot_response('goodbye', [])
        reprompt_text = speech_output
        should_end_session = True
        if speech_output == 'Please specify some other choices!':
            should_end_session = False
        return build_response(session_attributes, 
                            build_speechlet_response(card_title,speech_output,reprompt_text,should_end_session))

    elif intent_name == "DenyIntent":
        speech_output = get_bot_response('deny', [])
        reprompt_text = speech_output
        if 'Nice talking' in speech_output:
            should_end_session = True
        return build_response(session_attributes, 
                            build_speechlet_response(card_title,speech_output,reprompt_text,should_end_session))

    elif intent_name == "SearchIntent":
        entities = []
        slots = intent_request['intent']['slots']
        Cuisine = slots['Cuisine'].get('resolutions', None)
        Price = slots['Price'].get('resolutions', None)
        Alcohol = slots['Alcohol'].get('resolutions', None)
        Smoking = slots['Smoking'].get('resolutions', None)
        if Cuisine:
            if Cuisine['resolutionsPerAuthority'][0]['status']['code']=='ER_SUCCESS_NO_MATCH':
                entities.append({'entity':'Cuisine','value':'None'})
            else:
                Cuisine = Cuisine['resolutionsPerAuthority'][0]['values'][0]['value']['name']
                entities.append({'entity': 'Cuisine', 'value': Cuisine.lower()})

        if Price:
            if Price['resolutionsPerAuthority'][0]['status']['code']=='ER_SUCCESS_NO_MATCH':
                entities.append({'entity':'Price','value':'None'})
            else:
                Price = Price['resolutionsPerAuthority'][0]['values'][0]['value']['name']
                entities.append({'entity': 'Price', 'value': Price.lower()})
            
        if Alcohol:
            if Alcohol['resolutionsPerAuthority'][0]['status']['code']=='ER_SUCCESS_NO_MATCH':
                entities.append({'entity':'Alcohol','value':'None'})
            else:
                value = Alcohol['resolutionsPerAuthority'][0]['values'][0]['value']['name']
                entity = 'Alcohol'
                if value == 'no booze':
                    Alcohol = 'No_Alcohol_Served'
                elif value == 'wine' or value == 'beer':
                    Alcohol = 'Wine-Beer'
                else:
                    Alcohol = 'Full_Bar'
                entities.append({'entity': entity, 'value': Alcohol})

        if Smoking:
            if Smoking['resolutionsPerAuthority'][0]['status']['code']=='ER_SUCCESS_NO_MATCH':
                entities.append({'entity':'Smoking','value':'None'})
            else:
                value = Smoking['resolutionsPerAuthority'][0]['values'][0]['value']['name']
                if value == 'smoking':
                    Smoking = 'permitted'
                elif value == 'no smoking':
                    Smoking = 'not permitted'
                else:
                    Smoking = 'section'
                entities.append({'entity': 'Smoking', 'value': Smoking})

        speech_output = get_bot_response('search', entities)
        reprompt_text = speech_output
        return build_response(session_attributes, 
                            build_speechlet_response(card_title,speech_output,reprompt_text,should_end_session))

    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()

    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()

    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    clear_vars()

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Restaurant Assistant. We are more than happy to help the foodie inside of you"
    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_help_response():
    session_attributes = {}
    card_title = "Help"
    speech_output = "To begin, you can say...show me a mexican place... or show me an inexpensive restaurant"
    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(card_title,speech_output,reprompt_text,should_end_session))

def handle_session_end_request():
    clear_vars()
    card_title = "Session Ended"
    speech_output = "Thank you for using the Restaurant Assistant! We hope you enjoyed the experience."
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

