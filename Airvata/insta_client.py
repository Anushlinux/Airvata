from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes
import time
import logging
import os
import random
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstagramClient:
    def __init__(self):
        self.client = Client()
        self.client.delay_range = [1, 3]  # Add random delay between requests
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.session_path = "instagram_session.json"
        
    def login(self):
        """Login to Instagram with session handling"""
        try:
            # Try to load session if exists
            if os.path.exists(self.session_path):
                self.client.load_settings(self.session_path)
                try:
                    self.client.get_timeline_feed()  # Test if session is valid
                    logger.info("Successfully loaded session")
                    return True
                except LoginRequired:
                    logger.info("Session expired, logging in again")
                    pass
                    
            # If session doesn't exist or is invalid, login with credentials
            self.client.login(self.username, self.password)
            self.client.dump_settings(self.session_path)
            logger.info("Login successful")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
            
    def handle_rate_limit(self, func, *args, **kwargs):
        """Wrapper to handle rate limiting"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except PleaseWaitFewMinutes:
                wait_time = 300 * (attempt + 1)  # Increase wait time with each attempt
                logger.warning(f"Rate limited. Waiting for {wait_time} seconds...")
                time.sleep(wait_time)
        
        logger.error(f"Failed after {max_attempts} attempts due to rate limiting")
        return None
    
    def get_pending_messages(self):
        """Get all unread messages"""
        inbox = self.handle_rate_limit(self.client.direct_inbox)
        if not inbox:
            return []
            
        pending_threads = []
        
        for thread in inbox.threads:
            # Get messages only for threads with unread messages
            if thread.unread_count > 0:
                # Add random delay to avoid spam detection
                time.sleep(random.uniform(1, 2))
                thread_details = self.handle_rate_limit(
                    self.client.direct_thread, thread.id
                )
                if thread_details:
                    pending_threads.append(thread_details)
                
        return pending_threads
    
    def reply_to_message(self, thread_id, text):
        """Send a reply to a specific thread"""
        return self.handle_rate_limit(
            self.client.direct_send, text, thread_ids=[thread_id]
        )
        
        
        
       
