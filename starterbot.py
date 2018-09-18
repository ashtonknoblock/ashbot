# -*- coding: utf-8 -*-
import os
import time
import re
import requests
import sys
import random
import string
import logging
import signal
import jokes
from slackclient import SlackClient

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

# while true, bot will be online and listening
running_flag = True
help_count = 0
# Get random jokes from jokes.py...
# NOT SURE if it will work if someone else tried dl-ing
joke = jokes.jokes


# setup the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('log.txt')
formatter = logging.Formatter(
    "%(asctime)s: %(levelname)s:    %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None


def signal_handler(sig_num, frame):
    """
            if we get a sigint or sigterm signal, exit program
    """
    global running_flag
    global start_time
    uptime = (time.time()-start_time)
    sigint_log = """SIGINT signal detected... Ashbot disconnected.
                \nUptime was {} seconds.\n\n""".format(uptime)

    sigterm_log = """SIGTERM signal detected...Disconnected.
                \nUptime was {} seconds.\n\n""".format(uptime)
    if sig_num == signal.SIGINT:
        logger.info(sigint_log)
        running_flag = False
    if sig_num == signal.SIGTERM:
        running_flag = False
        logger.info(sigterm_log)
    return None


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
        If there is no direct mention, returns None.
    """
    matches = re.search(MENTION_REGEX, message_text)
    if matches:
        recieved_message = matches.group(2).strip()
        logger.info("messege RECIEVED '{}'".format(recieved_message))
    return (matches.group(1),
            recieved_message) if matches else (None, None)


def cleaning(text):
    """
        Takes received message, and removes
        new lines, punctuation, white space, and any capitalization
    """
    # don't parse special commands
    if text != "As-salamu alaykum":
        ex = set(string.punctuation)

        # remove new line and digits with regular expression
        text = re.sub(r'\n', '', text)
        # remove non-ascii characters
        text = ''.join(character for character in text if ord(character) < 128)
        # remove punctuations
        text = ''.join(character for character in text if character not in ex)
        # standardize white space
        text = re.sub(r'\s+', ' ', text)
        # drop capitalization
        text = text.lower()
        # remove white space around front and back
        text = text.strip()

    else:
        pass
    return text


def handle_command(command, channel):
    """
        Executes bot command
    """
    global help_count
    global start_time
    global running_flag
    uptime = (time.time()-start_time)
    random_joke = random.choice(joke)
    help_response = """*Available commands are:*
`help-- display commands you can tell me.`
`ping-- check if/how long I've been active`
`whats on your mind-- ???`
`quit-- make me exit and stop listening`
`exit-- same a quit`
    """
    exit_response = """
Life and destiny can steal my best friend away from me
 but nothing can take away the precious memories.
 Goodbye my friend.
"""
    command = cleaning(command)
    # default message for unknown message
    default_response = "Not sure what you mean. Try *help*."

    # Finds and executes the given command, filling in response
    response = None
    # Here we can create our responses
    if command == 'help' or command.startswith('help'):
        if help_count == 0:
            response = help_response
        if help_count == 1:
            response = "I've already told you once." + "\n" + help_response
        if help_count >= 2:
            count_resp = "{}".format(help_count) + "\n" + help_response
            response = "I've already told you *{}* times".format(count_resp)
        help_count += 1

    elif command == 'ping':
        response = "Ashbot is active. Uptime: {} seconds".format(uptime)

    elif command == "hey" or command == "hi" or command == "hello":
        response = "Aloha"

    elif command == "yo" or command == "whats up":
        response = "What's up?"

    elif command == 'k':
        response = "k"

    elif command == "whats on your mind":
        response = "{}".format(random_joke)

    elif command == "thanks" or command == "thank you":
        response = "Don't mention it.\nSeriously."

    elif command == "as-salamu alaykum":
        response = "wa ʿalaykumu s-salām"

    elif command == 'quit' or command == "exit":
        response = exit_response
        # send a sigterm signal to shutdown the bot
        os.kill(os.getpid(), signal.SIGTERM)

    responses = response or default_response

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=responses
    )

    logger.info("RESPONSE: '{}'\n".format(responses))


if __name__ == "__main__":
    """     below are urls for each channel. Whichever one is used,
            the bot will announce itself to the channel that it's online
    """
    logger.info('Connecting...')
    channel_random_url = '''
https://hooks.slack.com/services/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
'''
    channel_test_url = '''
https://hooks.slack.com/services/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
'''
    payload = {"text": "sup"}
    start_time = time.time()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if slack_client.rtm_connect(with_team_state=False):
        logger.info('Connected to channel. listening...')
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        # announce to the channel that we're online
        r = requests.post(channel_test_url, json=payload)

        # true unless sigint or sigterm signal is sent
        while running_flag:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            try:
                if command:
                    handle_command(command, channel)
                    time.sleep(RTM_READ_DELAY)

            except Exception:
                logger.exception("EXCEPTION")
    else:
        logger.info("Ashbot can't connect. Shutting down.")
        sys.exit()
