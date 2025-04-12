# instagram_client.py
import os
import time
import logging
import random
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, ClientForbiddenError

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstagramClient:
    def __init__(self):
        self.client = Client()
        self.client.delay_range = [2, 5] # Crucial: Random delay between API calls
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.session_path = "instagram_session.json"
        self.user_id = None

    def login(self):
        logger.info("Attempting Instagram login...")
        try:
            if os.path.exists(self.session_path):
                self.client.load_settings(self.session_path)
                self.client.login(self.username, self.password) # Still need login to validate session
                logger.info("Session loaded and validated.")
            else:
                self.client.login(self.username, self.password)
                self.client.dump_settings(self.session_path)
                logger.info("Logged in successfully and session saved.")
            self.user_id = self.client.user_id # Store own user ID
            return True
        except LoginRequired:
             logger.warning("Session expired or invalid. Attempting fresh login.")
             try:
                 self.client.login(self.username, self.password)
                 self.client.dump_settings(self.session_path)
                 self.user_id = self.client.user_id
                 logger.info("Fresh login successful and session saved.")
                 return True
             except Exception as e:
                 logger.error(f"Fresh login failed: {e}", exc_info=True)
                 return False
        except Exception as e:
            logger.error(f"Instagram login failed: {e}", exc_info=True)
            return False

    def _handle_api_call(self, func, *args, **kwargs):
        """Wrapper for instagrapi calls with rate limit handling"""
        try:
            # Add a small random delay before each call
            time.sleep(random.uniform(1.5, 3.5))
            return func(*args, **kwargs)
        except PleaseWaitFewMinutes:
            logger.warning("Rate limit hit (PleaseWaitFewMinutes). Waiting 5 minutes...")
            time.sleep(300)
            return func(*args, **kwargs) # Retry after waiting
        except ClientForbiddenError as e:
             logger.error(f"ClientForbiddenError: {e}. This might be due to restrictions or detection.", exc_info=True)
             # Potentially wait longer or stop for this user/thread
             time.sleep(600) # Wait 10 mins before potentially trying again
             return None # Indicate failure
        except Exception as e:
            logger.error(f"An error occurred during API call {func.__name__}: {e}", exc_info=True)
            return None # Indicate failure

    def get_unread_threads(self):
        logger.info("Checking for unread messages...")
        inbox = self._handle_api_call(self.client.direct_inbox, amount=20) # Fetch recent threads
        if not inbox:
            logger.warning("Could not fetch direct inbox.")
            return []

        unread_threads_details = []
        for thread in inbox.threads:
            if thread.unread_count > 0:
                logger.info(f"Found unread messages in thread {thread.id}.")
                # Fetch full thread details to get actual messages
                thread_detail = self._handle_api_call(self.client.direct_thread, thread.id, amount=20)
                if thread_detail:
                    unread_threads_details.append(thread_detail)
                else:
                    logger.warning(f"Could not fetch details for thread {thread.id}")

        logger.info(f"Found {len(unread_threads_details)} threads with new messages.")
        return unread_threads_details

    def send_direct_message(self, thread_id: str, text: str):
        logger.info(f"Attempting to send message to thread {thread_id}...")
        result = self._handle_api_call(self.client.direct_send, text, thread_ids=[thread_id])
        if result:
            logger.info(f"Successfully sent message to thread {thread_id}")
            return True
        else:
            logger.error(f"Failed to send message to thread {thread_id}")
            return False
