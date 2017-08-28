from __future__ import print_function
from random import randint
from re import compile as regex_compile
import traceback
import sys

regex = regex_compile("<([^>]+)>")



# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    if output[:7] == "<speak>" and output[-8:] == "</speak>":
        speach_type = 'SSML'
    else:
        speach_type='PlainText'
    speach_key = 'text' if speach_type == 'PlainText' else 'ssml'
    return {
        'outputSpeech': {
            'type': speach_type,
            speach_key: output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output if speach_type == 'PlainText' else regex.sub('', output)
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


# --------------- Functions that control the skill's behavior ------------------

def generate_next_number(base, step=3, goal=21):
    try:
        return randint(base + 1, min(base + step, goal))
    except ValueError:
        return 0

def set_first_player(user_first):
    card_title = "Count Game"
    reprompt_text = "Please say a number."
    if user_first:
        current_sum = 0
        speech_output = "OK. Please say a number."
    else:
        current_sum = generate_next_number(0)
        speech_output = "OK. %s. Please say a number." % current_sum
    session_attributes = {
        'asking_first': False,
        'current_sum': current_sum
    }
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def ask_for_first_player():
    session_attributes = {
        'asking_first': True
    }
    card_title = "Let's start!"
    speech_output = "Do you want to start first?"
    reprompt_text = "Do you want to start first? Please say YES or NO."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_propose_number_request(intent, session):
    current_sum = session.get('attributes', {}).get('current_sum', 1000)
    num = int(intent.get("slots", {}).get("num", {}).get("value", -1))
    diff = num - current_sum
    if diff not in [1, 2, 3] or num > 21 or num <= 0:
        session_attributes = {
            'current_sum': current_sum
        }
        card_title = "Invalid number!"
        speech_output = "%s is the current sum. %s is not a valid number to propose for the game." % (current_sum, num)
        reprompt_text = speech_output
        should_end_session = False
    elif num == 21:
        session_attributes = {}
        card_title = "You loose the game!"
        speech_output = "Oh, you loose the game!"
        reprompt_text = ""
        should_end_session = True
    else:
        new_sum = generate_next_number(num)
        session_attributes = {
            'current_sum': new_sum
        }
        if new_sum == 21:
            card_title = "You win!"
            speech_output = "<speak>21. <break time=\"1s\"/> Wow! You win! Congratulations!</speak>"
            reprompt_text = ""
            should_end_session = True
        else:
            card_title = "Count Game"
            speech_output = "%s" % new_sum
            reprompt_text = "Please say a number"
            should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def start_game():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {
        'asking_first': True
    }
    card_title = "Let's start!"
    speech_output = "<speak>OK. Let's play the count to twenty one game. " \
                    "Starting from 0, in turn we add 1, 2, or 3 to the current sum," \
                    "and say the new sum out. " \
                    "Whoever counts to 21 looses the game. " \
                    "<break time=\"1s\"/>" \
                    "Do you want to start first?</speak>"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Do you want to start first? Please say YES or NO."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}


def set_color_in_session(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    if 'Color' in intent['slots']:
        favorite_color = intent['slots']['Color']['value']
        session_attributes = create_favorite_color_attributes(favorite_color)
        speech_output = "I now know your favorite color is " + \
                        favorite_color + \
                        ". You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
        reprompt_text = "You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your favorite color is. " \
                        "You can tell me your favorite color by saying, " \
                        "my favorite color is red."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    session_attributes = {}
    reprompt_text = None
    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False
    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return start_game()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    # Dispatch to your skill's intent handlers
    if intent_name in ["StartGameIntent", "LaunchNativeAppIntent"]:
        return on_launch(intent_request, session)
    elif intent_name == "WhatsMyColorIntent":
        return get_color_from_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return start_game()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "ProposeNumberIntent":
        return handle_propose_number_request(intent, session)
    elif session.get('attributes', {}).get('asking_first'):
        if intent_name in ["UserFirstIntent", "UserSecondIntent"]:
            return set_first_player(intent_name == "UserFirstIntent")
        else:
            return ask_for_first_player()
    else:
        return "invalid intent %s" % intent_name
        raise ValueError("Invalid intent %s" % intent_name)


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    try:
        """ Route the incoming request based on type (LaunchRequest, IntentRequest,
        etc.) The JSON body of the request is provided in the event parameter.
        """
        print("event.session.application.applicationId=" +
              event['session']['application']['applicationId'])
        """
        Uncomment this if statement and populate with your skill's application ID to
        prevent someone else from configuring a skill that sends requests to this
        function.
        """
        # if (event['session']['application']['applicationId'] !=
        #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
        #     raise ValueError("Invalid Application ID")
        if event['session']['new']:
            on_session_started({'requestId': event['request']['requestId']},
                               event['session'])
        if event['request']['type'] == "LaunchRequest":
            return on_launch(event['request'], event['session'])
        elif event['request']['type'] == "IntentRequest":
            return on_intent(event['request'], event['session'])
        elif event['request']['type'] == "SessionEndedRequest":
            return on_session_ended(event['request'], event['session'])
    except Exception as e:
        return error_response(e)

# --------------- Debug ------------------

def error_response(e):
    card_title = "Error Response"
    exc_type, exc_obj, exc_tb = sys.exc_info()
    speech_output = "<speak>This is an error response." \
                    "Exception type is <break time=\"0.5s\"/> %s. <break time=\"0.5s\"/>" \
                    "Exception message is <break time=\"0.5s\"/> %s. <break time=\"0.5s\"/>" \
                    "The exception occured at the line <break time=\"0.5s\"/> %s <break time=\"0.5s\"/> of function <break time=\"0.5s\"/> %s. </speak>" % (
                        str(e.__class__)[7:-2],
                        e.message,
                        traceback.extract_tb(exc_tb)[-1][1],
                        traceback.extract_tb(exc_tb)[-1][0],
                    )
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def debug_response(e):
    card_title = "Debug Response"
    speech_output = "This is a debug response. Your session is ended. Exception type is %s. Message is %s" % (str(e.__class__)[7:-2], e.message)
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))