# main.py
import time
import logging
import os
import re # Import the regular expression module
from dotenv import load_dotenv
from insta_client import InstagramClient
from agent import ADKAgent
from dm_handler import MessageHandler

# --- Logging Setup ---
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger() # Root logger
logger.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# File Handler (optional)
# file_handler = logging.FileHandler("instagram_bot.log")
# file_handler.setFormatter(log_formatter)
# logger.addHandler(file_handler)
# --- End Logging Setup ---

def main():
    load_dotenv()
    logger.info("Starting Instagram ADK Bot...")

    # --- Initialization ---
    try:
        instagram_client = InstagramClient()
        if not instagram_client.login():
            logger.critical("Instagram login failed. Cannot continue.")
            return # Exit if login fails

        ai_agent = ADKAgent() # Raises error if API key is missing

        message_handler = MessageHandler(instagram_client, ai_agent)

    except Exception as e:
        logger.critical(f"Initialization failed: {e}", exc_info=True)
        return
    # --- End Initialization ---


    # --- Main Loop ---
    # Clean and convert the check interval from environment variable
    check_interval_str = os.getenv("CHECK_INTERVAL_SECONDS", "60")
    # Remove non-digit characters using regex
    cleaned_interval_str = re.sub(r'\D', '', check_interval_str)
    try:
        # Use 60 as default if cleaning results in an empty string or conversion fails
        check_interval = int(cleaned_interval_str) if cleaned_interval_str else 60
    except ValueError:
        logger.warning(f"Invalid value '{check_interval_str}' for CHECK_INTERVAL_SECONDS. Using default 60.")
        check_interval = 60

    logger.info(f"Initialization complete. Starting main loop (checking every {check_interval} seconds).")

    try:
        while True:
            logger.debug("Starting message processing cycle...")
            message_handler.process_unread_messages()
            logger.debug(f"Message processing cycle finished. Sleeping for {check_interval} seconds...")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred in the main loop: {e}", exc_info=True)
    finally:
        # Perform any cleanup here if needed
        logger.info("Instagram ADK Bot shutting down.")
    # --- End Main Loop ---

if __name__ == "__main__":
    main()