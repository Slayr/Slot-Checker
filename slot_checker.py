# This script has been refactored to use the 'requests' and 'beautifulsoup4' libraries,
# removing the need for Selenium and a Chrome browser. This makes it much more lightweight
# and suitable for running on low-resource devices like a Raspberry Pi.
#
# Make sure to install the required libraries:
# pip install requests beautifulsoup4

import smtplib
import time
import logging
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

# --- CONFIGURATION VARIABLES ---
# Credentials
USERNAME = "251280070011"  # Your registration number
PASSWORD = "07/10/2002"  # Your portal password

# Email Notification Settings
SENDER_EMAIL = "kidemporer@gmail.com"  # Your Gmail address
SENDER_PASSWORD = "rwsm uoyv acvb aonc"  # Your Gmail App Password
RECEIVER_EMAILS = ["kidemporer@gmail.com", "r.brinda.in@gmail.com", "brindaprabhu355@gmail.com", "allanavasn@gmail.com", "allanavas16@gmail.com"]  # List of email addresses to receive notifications

# Script Settings
CHECK_INTERVAL = 300  # Time in seconds between checks (e.g., 300 for 5 minutes)

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def send_email(subject, body):
    """
    Sends an email with a given subject and body.
    """
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAILS]):
        logging.warning("Email credentials not fully configured. Skipping notification.")
        return

    logging.info(f"Preparing to send email notification: {subject}")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECEIVER_EMAILS)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        logging.info("Email notification sent successfully!")
    except smtplib.SMTPAuthenticationError:
        logging.error("Failed to send email. Check SENDER_EMAIL and SENDER_PASSWORD (App Password).")
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending email: {e}")


def get_asp_net_fields(soup):
    """Extracts __VIEWSTATE and __EVENTVALIDATION from a BeautifulSoup object."""
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})

    if not viewstate:
        raise ValueError("Could not find __VIEWSTATE in the page.")
    if not eventvalidation:
        # This might not always be present, so handle its absence gracefully
        logging.warning("Could not find __EVENTVALIDATION in the page.")
        return viewstate['value'], ''

    return viewstate['value'], eventvalidation['value']


def main():
    """
    Main function to run the slot checker.
    """
    if not all([USERNAME, PASSWORD]):
        logging.error("USERNAME and PASSWORD must be set in the script.")
        return

    send_email("Slot Checker Initialized", f"The Manipal slot checker script has started at {time.strftime('%Y-%m-%d %H:%M:%S')}.")

    site_reachable_email_sent = False
    site_down_email_sent = False
    base_url = "https://portal.manipal.edu/statistics/"
    initial_url = f"{base_url}I11"

    while True:
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })

            # --- Step 1: Get initial page to select role ---
            logging.info(f"Navigating to {initial_url} to select role.")
            response = session.get(initial_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Site is reachable
            if not site_reachable_email_sent:
                send_email("Manipal Portal is Reachable", "The script has successfully connected to the portal and will now attempt to log in.")
                site_reachable_email_sent = True
            if site_down_email_sent:
                send_email("Manipal Portal is Back Online", "The script can connect to the portal again. Monitoring will resume.")
                site_down_email_sent = False

            viewstate, eventvalidation = get_asp_net_fields(soup)

            # --- Step 2: Select role 'S' (Student) ---
            logging.info("On landing page. Selecting role...")
            role_payload = {
                '__EVENTTARGET': '', '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate, '__EVENTVALIDATION': eventvalidation,
                'ddlrole': 'S', 'btncontinue': 'Continue'
            }
            response = session.post(initial_url, data=role_payload, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            logging.info("Role selected. Proceeding to login.")

            # --- Step 3: Log in ---
            logging.info("On login page. Submitting credentials...")
            viewstate, eventvalidation = get_asp_net_fields(soup)
            login_payload = {
                '__EVENTTARGET': '', '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate, '__EVENTVALIDATION': eventvalidation,
                'txtrollno': USERNAME, 'txtstudpwd': PASSWORD, 'studlogin': 'Login'
            }
            
            # Post to the same URL we got the form from
            response = session.post(response.url, data=login_payload, allow_redirects=True, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            welcome_element = soup.find(id="lblnm")
            if not welcome_element:
                logging.error("Login failed. Could not find welcome message. Check credentials or if the portal has changed.")
                with open("login_failure_page.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                logging.error("Saved page source for login failure. Retrying main loop...")
                time.sleep(CHECK_INTERVAL)
                continue
            
            logging.info(f"Login successful! Welcome {welcome_element.text.strip()}.")

            # --- Step 4: Check Availability Loop ---
            consultation_url = f"{base_url}I7"
            logging.info(f"On I7 page ({consultation_url}). Starting availability check loop.")
            
            while True:
                logging.info("Refreshing I7 page to check for new slots...")
                response = session.get(consultation_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                table = soup.find('table', id='grdupevents')
                if table:
                    # Find any checkbox input that is NOT disabled.
                    # The presence of the 'disabled' attribute means it's disabled.
                    # We look for a checkbox that does not have that attribute.
                    enabled_checkbox = table.find('input', type='checkbox', disabled=None)
                    
                    if enabled_checkbox:
                        logging.info("SUCCESS: Enabled checkbox found, indicating an available slot!")
                        send_email("Consultation Slot Available!", "An appointment slot has opened up on the Manipal portal. Please log in to book it.")
                        logging.info("Script finished after finding a slot. Exiting.")
                        return  # Exit the program
                    else:
                        logging.info("Did not find an enabled checkbox on this check. No new slots available.")
                else:
                    logging.warning("Could not find the 'grdupevents' table on the page. Website structure might have changed.")

                logging.info(f"Waiting for {CHECK_INTERVAL} seconds before the next check...")
                time.sleep(CHECK_INTERVAL)

        except requests.exceptions.RequestException as e:
            logging.error(f"A network error occurred: {e}. Retrying after interval.")
            if not site_down_email_sent:
                send_email("Manipal Portal Unreachable", f"The script could not access the Manipal portal due to a network error: {e}. It will keep retrying.")
                site_down_email_sent = True
                site_reachable_email_sent = False
        except (ValueError, KeyError, AttributeError) as e:
            logging.error(f"Failed to parse page HTML: {e}. The website structure may have changed. Retrying...")
            if not site_down_email_sent:
                send_email("Manipal Portal Structure Change?", f"The script failed to parse the page HTML, which may indicate a website update. Error: {e}. It will keep retrying.")
                site_down_email_sent = True
                site_reachable_email_sent = False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}. Retrying after interval.")
            if not site_down_email_sent:
                send_email("Manipal Portal Unreachable (Unexpected Error)", f"The script encountered an unexpected error: {e}. It will keep retrying.")
                site_down_email_sent = True
                site_reachable_email_sent = False
        
        logging.info(f"Waiting for {CHECK_INTERVAL} seconds before restarting the process.")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
