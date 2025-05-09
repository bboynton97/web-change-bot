import os

import requests
from bs4 import BeautifulSoup
import time
from twilio.rest import Client
import logging
from fuzzywuzzy import fuzz
from datetime import datetime
import pytz
from dotenv import load_dotenv
import difflib
from openai import OpenAI

load_dotenv()
openai = OpenAI()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_PHONE_NUMBER = os.getenv('TO_PHONE_NUMBER')
TO_PHONE_NUMBERS = [TO_PHONE_NUMBER]

if ',' in TO_PHONE_NUMBER:
    TO_PHONE_NUMBERS = TO_PHONE_NUMBER.split(',')

URLS = os.getenv('URLS_TO_MONITOR').split(',')
FREQUENCY_IN_SECONDS = int(os.getenv('FREQUENCY_IN_SECONDS'))

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
        with open(f"{file}.txt", 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def write_state(file, state):
    with open(f"{file}.txt", 'w') as f:
        f.write(state)


def send_sms(client, from_number, to_number, message):
    client.messages.create(
        body=message,
        from_=from_number,
        to=to_number
    )


def string_diff(str1, str2):
    differ = difflib.Differ()
    diff = differ.compare(str2.splitlines(keepends=True), str1.splitlines(keepends=True))

    return ''.join(diff)


def summarize_diff(diff):
    try:
        messages = [{"role": "system", "content": "you are a text diff summarization tool. explain the important parts of the diff in a very short summary. only mention changes, not text that didn't change. this is a diff on an ecommerce website selling cute bodysuits."},
                               {"role": "user", "content": diff}]
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
        )

        return response.choices[0].message.content
    except Exception as e:
        print('Failed to get diff: ', e)
        return ''



def clean_url(url: str):
    url = url.replace('https://', '')
    url = url.replace('/', '')
    url = url.replace('.', '')
    return url


# Files to store the last known state of the website
for url in URLS:
    cleaned_url = clean_url(url)
    STATE_FILE = f'{cleaned_url}.txt'
    if not os.path.isfile(STATE_FILE):
        with open(STATE_FILE, 'w') as f:
            pass


def main():
    counter = 0
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    while True:
        try:
            for url in URLS:
                last_state = read_last_state(clean_url(url))
                current_state = get_website_content(url)

                if current_state != last_state:
                    percent_change = compare_strings(current_state, last_state)
                    percent_change = 100 - percent_change
                    logger.info("Change detected on the website - {}% different".format(percent_change))
                    diff = string_diff(current_state, last_state)
                    print(f"Changes detected on website:\n {diff}")

                    if percent_change > 2:
                        diff_summary = summarize_diff(diff)

                        for number in TO_PHONE_NUMBERS:
                            if counter == 0:
                                send_sms(client, TWILIO_PHONE_NUMBER, number,
                                        f"Web change bot reset. Tracking {url} every {FREQUENCY_IN_SECONDS} seconds 💅🏻")
                            else:
                                send_sms(client, TWILIO_PHONE_NUMBER, number,
                                        f"Change detected on {url} - {percent_change}% different. \n Summary: {diff_summary}")

                    write_state(clean_url(url), current_state)
                else:
                    logger.info(
                        f"No change detected for {url} at {datetime.now(pytz.timezone('UTC')).astimezone(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
                    pass

            counter += 1
            time.sleep(FREQUENCY_IN_SECONDS)  # Check every 60 seconds

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            for number in TO_PHONE_NUMBERS:
                send_sms(client, TWILIO_PHONE_NUMBER, number,
                     "An unknown exception occurred while checking for website changes.")
            time.sleep(FREQUENCY_IN_SECONDS)


if __name__ == "__main__":
    main()
