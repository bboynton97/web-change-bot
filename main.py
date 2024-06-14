import os

import requests
from bs4 import BeautifulSoup
import time
from twilio.rest import Client
import logging
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_PHONE_NUMBER = os.getenv('TO_PHONE_NUMBER')
TO_PHONE_NUMBERS = [TO_PHONE_NUMBER]

if ',' in TO_PHONE_NUMBER:
    TO_PHONE_NUMBERS = TO_PHONE_NUMBER.split(',')

URL = os.getenv('URL_TO_MONITOR')
FREQUENCY_IN_SECONDS = int(os.getenv('FREQUENCY_IN_SECONDS'))

# File to store the last known state of the website
STATE_FILE = 'website_state.txt'
if not os.path.isfile(STATE_FILE):
    with open(STATE_FILE, 'w') as f:
        pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_website(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def compare_strings(str1, str2):
    return fuzz.ratio(str1, str2)


def get_website_content(url):
    html = fetch_website(url)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()


def read_last_state(file):
    try:
        with open(file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def write_state(file, state):
    with open(file, 'w') as f:
        f.write(state)


def send_sms(client, from_number, to_number, message):
    client.messages.create(
        body=message,
        from_=from_number,
        to=to_number
    )


def main():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    last_state = read_last_state(STATE_FILE)

    while True:
        try:
            current_state = get_website_content(URL)

            if current_state != last_state:
                percent_change = compare_strings(current_state, last_state)
                logger.info("Change detected on the website - {}% different".format(100-percent_change))

                for number in TO_PHONE_NUMBERS:
                    send_sms(client, TWILIO_PHONE_NUMBER, number, f"Change detected on {URL} - {100-percent_change}% different")

                write_state(STATE_FILE, current_state)
                last_state = current_state
            else:
                # logger.info("No change detected")
                pass

            time.sleep(FREQUENCY_IN_SECONDS)  # Check every 60 seconds

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            time.sleep(FREQUENCY_IN_SECONDS)


if __name__ == "__main__":
    main()
