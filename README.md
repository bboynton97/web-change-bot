## README

### Script Overview

This script monitors a specified website for changes and sends an SMS notification via Twilio when a change is detected. It compares the current state of the website with the last known state and uses fuzzy string matching to determine the difference. The script continuously checks the website at a user-defined interval.

### Prerequisites

- Python 3.x
- `requests` library
- `BeautifulSoup` from `bs4` library
- `twilio` library
- `fuzzywuzzy` library
- `python-dotenv` library

### Setup

1. **Install Required Libraries**

   Install the necessary Python libraries using pip:

   ```bash
   pip install requests beautifulsoup4 twilio fuzzywuzzy python-dotenv
   ```

2. **Twilio Account**

   Set up a Twilio account and obtain your Account SID and Auth Token. Also, create a Twilio phone number.

3. **Environment Variables**

   Create a `.env` file in the same directory as the script with the following contents:

   ```env
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   TO_PHONE_NUMBER=destination_phone_number
   URLS_TO_MONITOR=the_website_url_to_monitor_comma_diliminated
   FREQUENCY_IN_SECONDS=60  # or any other interval in seconds
   ```

### Usage

1. **Prepare the State File**

   Ensure there is a file named `website_state.txt` in the same directory as the script. This file will store the last known state of the website. If the file does not exist, the script will create it.

2. **Run the Script**

   Execute the script by running:

   ```bash
   python main.py
   ```

   Replace `main.py` with the actual name of your script file.

### Customization

You can customize the monitoring frequency, target URL, and notification message by modifying the environment variables or the script directly.