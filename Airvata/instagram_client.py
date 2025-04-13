import os
import time
import logging
import random
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes

load_dotenv()
logger = logging.getLogger(__name__)

class InstagramClient:
    def __init__(self):
        self.client = Client()
        self.client.delay_range = [2, 5]  # Add random delay between requests
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.session_path = "instagram_session.json"
        self.user_id = None
        
    def login(self):
        """Login to Instagram with session handling"""
        logger.info("Attempting Instagram login...")
        try:
            # Try to load session if exists
            if os.path.exists(self.session_path):
                self.client.load_settings(self.session_path)
                try:
                    # Test if session is valid
                    self.client.get_timeline_feed()
                    self.user_id = self.client.user_id
                    logger.info(f"Successfully loaded session. User ID: {self.user_id}")
                    return True
                except LoginRequired:
                    logger.info("Session expired, logging in again")
            
            # If session doesn't exist or is invalid, login with credentials
            self.client.login(self.username, self.password)
            self.client.dump_settings(self.session_path)
            self.user_id = self.client.user_id
            logger.info(f"Login successful. User ID: {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
            
    def get_unread_threads(self, amount=20):
        """Get unread threads using the correct method from docs"""
        logger.info("Checking for unread messages...")
        try:
            # Add a small delay to avoid API limits
            time.sleep(random.uniform(1, 3))
            # This returns threads with unread messages
            threads = self.client.direct_threads(
                amount=amount,
                selected_filter="unread"  # Filter for unread threads only
            )
            logger.info(f"Found {len(threads)} threads with unread messages")
            return threads
        except PleaseWaitFewMinutes:
            logger.warning("Rate limited. Waiting 5 minutes...")
            time.sleep(300)
            return []
        except Exception as e:
            logger.error(f"Error fetching unread threads: {e}")
            return []
    
    def send_reply(self, thread_id, text):
        """Send a reply using direct_answer method from docs"""
        logger.info(f"Sending reply to thread {thread_id}")
        try:
            # Add a small delay to avoid API limits
            time.sleep(random.uniform(1, 3))
            # This sends a reply to an existing thread
            result = self.client.direct_answer(thread_id, text)
            logger.info(f"Successfully sent reply to thread {thread_id}")
            return True
        except PleaseWaitFewMinutes:
            logger.warning("Rate limited. Waiting 5 minutes...")
            time.sleep(300)
            return False
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False
