
import os
import smtplib
import time
import logging
import shutil
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
HEADLESS_MODE = True  # Set to False to see the browser UI for debugging

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def find_chrome_binary():
    """
    Finds the Chrome/Chromium binary on a Linux system.
    """
    logging.info("Attempting to locate Chrome/Chromium binary...")
    # 1. Check system PATH
    binary_path = shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chromium")
    if binary_path:
        logging.info(f"Found Chrome binary in system PATH: {binary_path}")
        return binary_path

    # 2. Check common Linux paths
    common_paths = [
        "/var/lib/flatpak/app/com.google.Chrome/x86_64/stable/00b35bf603cc3cd9da9d89479e022b0b4b251ca469059b645fff721b39add583/files/extra/google-chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
        "/var/lib/flatpak/exports/bin/org.chromium.Chromium",
    ]
    for path in common_paths:
        if os.path.exists(path):
            logging.info(f"Found Chrome binary in common path: {path}")
            return path

    logging.error("Could not find Chrome/Chromium binary. Please ensure it's installed and in your PATH.")
    return None


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


def main():
    """
    Main function to run the slot checker.
    """
    if not all([USERNAME, PASSWORD]):
        logging.error("USERNAME and PASSWORD must be set in the script.")
        return

    send_email("Slot Checker Initialized", f"The Manipal slot checker script has started at {time.strftime('%Y-%m-%d %H:%M:%S')}.")

    chrome_binary_path = find_chrome_binary()
    if not chrome_binary_path:
        return

    site_reachable_email_sent = False
    site_down_email_sent = False
    url = "https://portal.manipal.edu/statistics/I11"

    while True:
        driver = None
        try:
            options = webdriver.ChromeOptions()
            options.binary_location = chrome_binary_path
            if HEADLESS_MODE:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

            # Use a generic Service object; Selenium 4 manages the driver automatically
            service = Service()

            driver = webdriver.Chrome(service=service, options=options)
            logging.info("WebDriver initialized successfully.")

            logging.info(f"Navigating to {url}")
            driver.get(url)

            # Site is reachable, send notifications if needed
            if not site_reachable_email_sent:
                send_email("Manipal Portal is Reachable", "The script has successfully connected to the portal and will now attempt to log in.")
                site_reachable_email_sent = True

            if site_down_email_sent:
                send_email("Manipal Portal is Back Online", "The script can connect to the portal again. Monitoring will resume.")
                site_down_email_sent = False

            # --- Step 1: Landing Page ---
            logging.info("On landing page. Selecting role...")
            wait = WebDriverWait(driver, 15)

            role_dropdown = wait.until(EC.presence_of_element_located((By.ID, "ddlrole")))
            Select(role_dropdown).select_by_value("S")

            continue_button = driver.find_element(By.ID, "btncontinue")
            continue_button.click()
            logging.info("Role selected and 'Continue' clicked.")

            # --- Step 2: Login Page ---
            logging.info("On login page. Waiting for student login form...")
            username_field = wait.until(EC.presence_of_element_located((By.ID, "txtrollno")))
            logging.info("Found username field (txtrollno). Entering username.")
            username_field.send_keys(USERNAME)

            password_field = driver.find_element(By.ID, "txtstudpwd")
            logging.info("Found password field (txtstudpwd). Entering password.")
            password_field.send_keys(PASSWORD)

            login_button = driver.find_element(By.ID, "studlogin")
            logging.info("Found login button (studlogin). Clicking.")
            login_button.click()
            logging.info("Login credentials submitted.")

            # Wait for the login to complete by looking for the welcome message element
            logging.info("Waiting for login to complete by verifying welcome message...")
            try:
                welcome_element = wait.until(EC.presence_of_element_located((By.ID, "lblnm")))
                logging.info(f"Login successful! Welcome {welcome_element.text}. Current URL: {driver.current_url}")
            except TimeoutException:
                logging.error("Login failed. Could not find welcome message after 15 seconds. Check credentials or network.")
                driver.save_screenshot("login_failure_screenshot.png")
                with open("login_failure_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logging.error("Saved screenshot and page source for login failure. Retrying main loop...")
                continue

            # Navigate to the Consultation Details (I7) page
            logging.info("Clicking 'more' link to navigate to Consultation Details (I7)...")
            try:
                more_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='more' and @href='I7']")))
                more_link.click()
                logging.info(f"Navigated to I7. Current URL: {driver.current_url}")
                wait.until(EC.presence_of_element_located((By.ID, "pnlgrid")))
            except TimeoutException:
                logging.error("Failed to navigate to Consultation Details (I7) page. 'more' link or 'pnlgrid' not found.")
                driver.save_screenshot("navigation_failure_screenshot.png")
                with open("navigation_failure_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logging.error("Saved screenshot and page source for navigation failure. Retrying main loop...")
                continue

            # --- Step 3: Check Availability ---
            logging.info("On I7 page. Starting availability check loop.")

            while True:
                try:
                    wait.until(EC.presence_of_element_located((By.ID, "pnlgrid")))
                    logging.info(f"Checking for slots. Current URL: {driver.current_url}")

                    screenshot_path = "debug_screenshot.png"
                    pagesource_path = "debug_page.html"
                    driver.save_screenshot(screenshot_path)
                    with open(pagesource_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logging.info(f"Saved screenshot to '{screenshot_path}' and page source to '{pagesource_path}'")

                    # Look for any checkboxes within the grid panel
                    xpath_selector = "//*[@id='pnlgrid']//input[@type='checkbox']"
                    logging.info(f"Checking for elements using XPath: {xpath_selector}")
                    checkboxes = driver.find_elements(By.XPATH, xpath_selector)

                    open_slot_found = False
                    for cb in checkboxes:
                        if cb.is_displayed() and cb.is_enabled():
                            open_slot_found = True
                            logging.info("SUCCESS: Enabled and visible checkbox found, indicating an available slot!")
                            break

                    if open_slot_found:
                        send_email("Consultation Slot Available!", "An appointment slot has opened up on the Manipal portal. Please log in to book it.")
                        logging.info("Script finished after finding a slot. Exiting.")
                        return
                    else:
                        logging.info("Did not find an enabled and visible checkbox on this check. No new slots available.")

                except NoSuchElementException:
                    logging.info("Did not find an enabled checkbox on this check. No new slots available.")
                    pass

                logging.info(f"Waiting for {CHECK_INTERVAL} seconds before the next check...")
                time.sleep(CHECK_INTERVAL)

                logging.info("Refreshing I7 page to check for new slots...")
                driver.refresh()

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"A Selenium error occurred: {e.__class__.__name__}. Retrying after interval.")
            if not site_down_email_sent:
                send_email("Manipal Portal Unreachable", f"The script could not access the Manipal portal due to a {e.__class__.__name__}. It will keep retrying.\n\nError: {e}")
                site_down_email_sent = True
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}. Retrying after interval.")
            if not site_down_email_sent:
                send_email("Manipal Portal Unreachable (Unexpected Error)", f"The script encountered an unexpected error: {e}. It will keep retrying.")
                site_down_email_sent = True
        finally:
            if driver:
                driver.quit()
                logging.info("WebDriver has been closed.")

        logging.info(f"Waiting for {CHECK_INTERVAL} seconds before retrying.")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
