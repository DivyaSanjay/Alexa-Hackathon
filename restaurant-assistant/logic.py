import sqlite3
import random

response, adr, params, suggestions, excluded = '', '', {}, [], []

responses = ["I'm sorry...I couldn't find anything like that. Can I help you with anything else?",
"{} is a great place, don't you think so?",
"does {} sound good?",
"{} seems perfect for you, doesn't it?",
'how do you feel about {}?',
"I think {} would be a splendid choice, don't you?"
 ]
 
random.seed(0)

def find_hotels(params, excluded):
    conn = sqlite3.connect("restaurants.db")
    c = conn.cursor()
    query = 'SELECT * FROM restaurants'
    if len(params) > 0:
        filters = ["{}=?".format(k) for k in params]
        print(filters)
        query += " WHERE " + " and ".join(filters)
    t = tuple(params.values())
    print(query)
    c.execute(query,t)
    data = list(c.fetchall())
    return data
    
def bot_answer(intent):
    if intent=='greet':
        response = "Hello to you too!"
    if intent=='goodbye':
        if adr == '?' or adr == '':
            response = "Nice talking to you! Have fun!"
        else:
            response = "Nice talking to you! The address is {}! Have fun!".format(adr)
    return response

def respond(params, suggestions, excluded, intent, entities):
    if intent == "greet" or intent=="goodbye":
        global response
        if 'Can I help you' in response:
            return 'Please specify some other choices!', '', {}, [], []
        response = bot_answer(intent)
        return response, '', {}, [], []
    if intent == "deny":
        global response
        if 'Can I help you' in response:
            return bot_answer('goodbye'), '', {}, [], []
        excluded.extend(suggestions)
    for ent in entities:
        params[ent["entity"]] = str(ent["value"])
    print(params)
    results = find_hotels(params, excluded)
    names = [r[1] for r in results if r[1] not in excluded]
    address = [ r[2] for r in results if r[1] not in excluded]
    if len(names)==0:
        n = 0
    elif len(names)==1:
        n = 1
    else:
        n = random.randint(2,5)
    suggestions = names[:1]
    adr = ''
    if suggestions:
        adr = address[:1][0]
    return responses[n].format(*suggestions), adr, params, suggestions, excluded

def get_bot_response(intent, entities):
    # Call the respond function
    print(entities)
    global response, adr, params, suggestions, excluded
    response, adr, params, suggestions, excluded = respond(params, suggestions, excluded, intent, entities)
    return response

def clear_vars():
    global adr, params, suggestions, excluded
    adr, params, suggestions, excluded = '', {}, [], []

