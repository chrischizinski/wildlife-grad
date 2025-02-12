import os
import logging
import requests

# Simple Slack notification function, as defined previously.
def send_slack_notification(message):
    webhook_url = os.environ.get("SLACK_WEBHOOK")
    if not webhook_url:
        logging.info("No SLACK_WEBHOOK environment variable set. Skipping Slack notification.")
        return
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload, headers={'Content-Type': 'application/json'})
        if response.status_code != 200:
            logging.error(f"Failed to send Slack notification: {response.status_code}, {response.text}")
        else:
            logging.info("Slack notification sent successfully.")
    except Exception as e:
        logging.error(f"Error sending Slack notification: {e}")

if __name__ == "__main__":
    # Send a test message
    send_slack_notification("Test Slack Notification: Wildlife Grad Job Scraper test message.")