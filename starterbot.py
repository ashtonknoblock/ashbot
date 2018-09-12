# -*- coding: utf-8 -*-
import os
import time
import re
import requests
import sys
import random
import string
from slackclient import SlackClient

running_flag = True

jokes = [
    'I asked God for a bike, but I know God doesn’t work that way. So I stole a bike and asked for forgiveness.',
    'Do not argue with an idiot. He will drag you down to his level and beat you with experience.',
    'I want to die peacefully in my sleep, like my grandfather.. Not screaming and yelling like the passengers in his car.',
    'The last thing I want to do is hurt you. But it’s still on the list.',
    'Light travels faster than sound. This is why some people appear bright until you hear them speak.',
    'If I agreed with you we’d both be wrong.',
    'The early bird might get the worm, but the second mouse gets the cheese.',
    'Politicians and diapers have one thing in common. They should both be changed regularly, and for the same reason.',
    'A bus station is where a bus stops. A train station is where a train stops. On my desk, I have a work station..',
    'Some people are like Slinkies … not really good for anything, but you can’t help smiling when you see one tumble down the stairs.',
    'How is it one careless match can start a forest fire, but it takes a whole box to start a campfire?',
    'To steal ideas from one person is plagiarism. To steal from many is research.',
    'Artificial intelligence is no match for natural stupidity.',
    'God must love stupid people. He made SO many.',
    'My opinions may have changed, but not the fact that I am right.',
    'You do not need a parachute to skydive. You only need a parachute to skydive twice.',
    'Nostalgia isn’t what it used to be.',
    'intend to live forever. So far, so good.',
    'With sufficient thrust, pigs fly just fine'
    ]


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to
        find bot commands.
        If a bot command is found, this function returns a tuple of
        command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in
        message text and returns the user ID which was mentioned.
        If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1),
             matches.group(2).strip()) if matches else (None, None)


def cleaning(text):
    """This function takes what ever text is sent to Ashbot, and makes
        it all evenly spaced lower case text without punctuation"""
    exclude = set(string.punctuation)

    # remove new line and digits with regular expression
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\d', '', text)
    # remove patterns matching url format
    url_pattern = r'((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?'
    text = re.sub(url_pattern, ' ', text)
    # remove non-ascii characters
    text = ''.join(character for character in text if ord(character) < 128)
    # remove punctuations
    text = ''.join(character for character in text if character not in exclude)
    # standardize white space
    text = re.sub(r'\s+', ' ', text)
    # drop capitalization
    text = text.lower()
    # remove white space around front and back
    text = text.strip()

    return text


def handle_command(command, channel):
    global start_time
    global running_flag

    random_joke = random.choice(jokes)

    help_response = """*Available commands are:*\n
        *help*-- display commands you can tell me.\n
        *ping*-- check if/how long I've been active\n
        *tell me a joke*-- you get it\n
        *quit*-- make me exit and stop listening\n
        *exit*-- same a quit\n
    """
    command = cleaning(command)

    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format('help')

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith('help'):
        response = help_response

    elif command == 'ping':
        response = "Ashbot is active. Uptime: {} seconds".format(time.time()-start_time)

    elif command == "hey" or command == "hi":
        response = "Hello friend."

    elif command == 'k':
        response = "k"

    elif command == 'tell me a joke':
        response = "{}".format(random_joke)

    elif command == "thanks" or command == "thank you":
        response = "Don't mention it."

    elif command == 'quit' or command == "exit":
        response = "Ashbot is now terminating!"
        running_flag = False

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    channel_random_url = 'https://hooks.slack.com/services/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'
    channel_test_url = 'https://hooks.slack.com/services/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'
    payload = {"text": "Hello, World!"}
    start_time = time.time()
    if slack_client.rtm_connect(with_team_state=False):
        print("Ashbot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        r = requests.post(channel_test_url, json=payload)

        while running_flag:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
        sys.exit()
