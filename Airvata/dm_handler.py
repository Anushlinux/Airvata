import json
import os
import logging
import time
import random
from instagram_client import InstagramClient
from ai_agent import AIAgent

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, instagram_client, ai_agent):
        self.instagram_client = instagram_client
        self.ai_agent = ai_agent
        self.processed_ids = {}  # {thread_id: set(message_ids)}
        self.conversation_history = {}  # {thread_id: [{sender, text, timestamp}]}
        self.processed_file = "processed_ids.json"
        self.history_file = "conversation_history.json"
        self.max_history = 10  # Max messages to keep per thread
        
        # Load saved state
        self.load_state()
    
    def load_state(self):
        """Load processed IDs and conversation history from files"""
        # Load processed IDs
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, "r") as f:
                    data = json.load(f)
                    # Convert lists to sets
                    self.processed_ids = {k: set(v) for k, v in data.items()}
                logger.info("Loaded processed message IDs from file")
            except Exception as e:
                logger.error(f"Error loading processed IDs: {e}")
                self.processed_ids = {}
        
        # Load conversation history
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    self.conversation_history = json.load(f)
                logger.info("Loaded conversation history from file")
            except Exception as e:
                logger.error(f"Error loading conversation history: {e}")
                self.conversation_history = {}
    
    def save_state(self):
        """Save processed IDs and conversation history to files"""
        # Save processed IDs
        try:
            # Convert sets to lists for JSON serialization
            data = {k: list(v) for k, v in self.processed_ids.items()}
            with open(self.processed_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving processed IDs: {e}")
        
        # Save conversation history
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.conversation_history, f)
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    def get_username_from_thread(self, thread, user_id):
        """Get username from user_id using thread.users"""
        if hasattr(thread, "users"):
            for user in thread.users:
                if hasattr(user, "pk") and str(user.pk) == str(user_id):
                    return user.username
        # Fallback if username not found
        return f"user_{user_id}"
    
    def process_messages(self):
        """Process all unread messages"""
        try:
            # Get unread threads
            unread_threads = self.instagram_client.get_unread_threads()
            if not unread_threads:
                return
            
            changes_made = False
            
            for thread in unread_threads:
                thread_id_str = str(thread.id)
                
                self.ai_agent.ensure_session(thread_id_str)
                
                # Initialize state for new threads
                if thread_id_str not in self.processed_ids:
                    self.processed_ids[thread_id_str] = set()
                if thread_id_str not in self.conversation_history:
                    self.conversation_history[thread_id_str] = []
                
                # Get unprocessed messages
                new_messages = []
                for msg in thread.messages:
                    # Check if message is not from bot and not already processed
                    if (hasattr(msg, "user_id") and 
                            msg.user_id != self.instagram_client.user_id and 
                            str(msg.id) not in self.processed_ids[thread_id_str]):
                        new_messages.append(msg)
                
                # Sort messages by timestamp (oldest first)
                new_messages.sort(key=lambda m: m.timestamp if hasattr(m, "timestamp") else 0)
                
                if not new_messages:
                    continue
                
                logger.info(f"Processing {len(new_messages)} new messages in thread {thread_id_str}")
                
                for message in new_messages:
                    changes_made = True
                    message_id = str(message.id)
                    
                    # Get sender username from thread.users
                    sender = self.get_username_from_thread(thread, message.user_id)
                    
                    # Get message text safely
                    message_text = getattr(message, "text", "") or ""
                    message_text = message_text.strip()
                    
                    if not message_text:
                        logger.info(f"Skipping empty or non-text message {message_id} from {sender} in thread {thread_id_str}")
                        # Mark as processed even if skipped
                        self.processed_ids[thread_id_str].add(message_id)
                        continue
                    
                    # Get conversation history for context
                    history = self.conversation_history[thread_id_str]
                    context = "\n".join([f"{m['sender']}: {m['text']}" for m in history[-self.max_history:]])
                    
                    # Generate response
                    response = self.ai_agent.generate_response(thread_id_str, message_text, context)
                    
                    # Send response if not None (not ignored)
                    if response:
                        success = self.instagram_client.send_reply(thread.id, response)
                        if success:
                            # Update conversation history
                            history.append({
                                "sender": sender,
                                "text": message_text,
                                "timestamp": str(message.timestamp)
                            })
                            history.append({
                                "sender": "bot",
                                "text": response,
                                "timestamp": str(int(time.time()))
                            })
                            
                            # Trim history if too long
                            if len(history) > self.max_history * 2:
                                self.conversation_history[thread_id_str] = history[-(self.max_history * 2):]
                            else:
                                self.conversation_history[thread_id_str] = history
                            
                            logger.info(f"Sent response to {sender} in thread {thread_id_str}")
                    
                    # Mark message as processed regardless of response
                    self.processed_ids[thread_id_str].add(message_id)
                    
                    # Add delay between messages
                    time.sleep(random.uniform(2, 5))
            
            # Save state if changes were made
            if changes_made:
                self.save_state()
                
        except Exception as e:
            logger.error(f"Error processing messages: {e}")
            # Try to save state even on error
            self.save_state()
