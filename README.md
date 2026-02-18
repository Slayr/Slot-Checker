# Slot Checker

This repository contains a Python script that checks for available slots on the Manipal portal and sends email notifications when a slot is found.

## Features

- Automated checking of the Manipal portal for slot availability.
- Email notifications to multiple recipients when a slot becomes available.
- Configurable check interval and headless browser mode.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Slayr/Slot-Checker.git
    cd Slot-Checker
    ```

2.  **Install dependencies:**
    ```bash
    pip install selenium
    ```
    You will also need a Chrome/Chromium browser installed on your system.

3.  **Configure the script:**
    Open `slot_checker.py` and update the following variables:
    -   `USERNAME`: Your registration number.
    -   `PASSWORD`: Your portal password.
    -   `SENDER_EMAIL`: Your Gmail address (used to send notifications).
    -   `SENDER_PASSWORD`: Your Gmail App Password (NOT your regular Gmail password). See [Google's documentation](https://support.google.com/accounts/answer/185833?hl=en) on how to generate one.
    -   `RECEIVER_EMAILS`: A list of email addresses to receive notifications (e.g., `["email1@example.com", "email2@example.com"]`).
    -   `CHECK_INTERVAL`: Time in seconds between checks.
    -   `HEADLESS_MODE`: Set to `True` to run the browser in the background, `False` to see the browser UI.

4.  **Run the script:**
    ```bash
    python slot_checker.py
    ```

## Troubleshooting

-   **Authentication Failed (Email):** Ensure `SENDER_PASSWORD` is a generated App Password, not your regular Gmail password.
-   **Chrome Binary Not Found:** Make sure Chrome or Chromium is installed and accessible in your system's PATH. The script attempts to find common paths, but you might need to adjust `find_chrome_binary` if it's in a non-standard location.
-   **Selenium Errors:** Check your internet connection and ensure the Manipal portal URL is correct and accessible. If running in headless mode, try setting `HEADLESS_MODE = False` to debug browser issues.