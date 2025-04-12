# message_handler.py
import json
import os
import logging
import random
import time
from insta_client import InstagramClient
from agent import ADKAgent

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, instagram_client: InstagramClient, ai_agent: ADKAgent):
        self.instagram_client = instagram_client
        self.ai_agent = ai_agent
        self.conversation_history = {}
        self.history_file = "conversation_history.json"
        self.max_history_per_thread = 20 # Keep last 20 messages per convo
        self.load_conversation_history()

    def load_conversation_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.conversation_history = json.load(f)
                logger.info("Loaded conversation history.")
            except json.JSONDecodeError:
                logger.error("Failed to decode conversation history JSON. Starting fresh.")
                self.conversation_history = {}
        else:
            logger.info("No conversation history file found. Starting fresh.")
            self.conversation_history = {}

    def save_conversation_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
            # logger.info("Saved conversation history.") # Can be noisy
        except Exception as e:
            logger.error(f"Failed to save conversation history: {e}", exc_info=True)

    def process_unread_messages(self):
        try:
            unread_threads = self.instagram_client.get_unread_threads()
            if not unread_threads:
                logger.info("No new messages to process.")
                return

            for thread in unread_threads:
                thread_id = thread.id
                if thread_id not in self.conversation_history:
                    self.conversation_history[thread_id] = []

                # Process messages in chronological order (oldest unread first)
                new_messages = sorted(
                    [msg for msg in thread.messages if not msg.is_seen and msg.user_id != self.instagram_client.user_id],
                    key=lambda msg: msg.timestamp
                )

                if not new_messages:
                    logger.info(f"Thread {thread_id} marked unread, but no new messages found (might be seen already).")
                    continue

                logger.info(f"Processing {len(new_messages)} new message(s) in thread {thread_id}")

                for message in new_messages:
                    # Prepare context (last N turns)
                    history = self.conversation_history.get(thread_id, [])
                    context_list = [f"{turn['sender']}: {turn['text']}" for turn in history[-self.max_history_per_thread:]]

                    sender_username = message.user.username # Get sender username for context/logging

                    # Get AI response
                    generated_response = self.ai_agent.generate_response(message.text, context_list)

                    if generated_response:
                        # Send the reply via Instagrapi client
                        success = self.instagram_client.send_direct_message(thread_id, generated_response)

                        if success:
                            # Update history ONLY if send was successful
                            history.append({"sender": sender_username, "text": message.text, "timestamp": str(message.timestamp)})
                            history.append({"sender": "bot", "text": generated_response, "timestamp": str(int(time.time()))})
                            # Trim history
                            self.conversation_history[thread_id] = history[-self.max_history_per_thread:]
                            logger.info(f"Successfully processed and replied to message from {sender_username} in thread {thread_id}")
                            # Mark message as seen (optional, Instagrapi might do this implicitly on reply)
                            # self.instagram_client._handle_api_call(self.instagram_client.client.direct_thread_mark_item_seen, thread_id, message.id)
                        else:
                            logger.error(f"Failed to send reply to {sender_username} in thread {thread_id}. History not updated for this turn.")
                            # Optional: Implement retry logic here
                    else:
                         logger.info(f"AI Agent decided to ignore message from {sender_username} in thread {thread_id}. No reply sent.")
                         # Still update history that we saw the message? Optional.
                         history.append({"sender": sender_username, "text": message.text + " [Ignored by Bot]", "timestamp": str(message.timestamp)})
                         self.conversation_history[thread_id] = history[-self.max_history_per_thread:]


                    # Small delay between processing messages within the same thread run
                    time.sleep(random.uniform(3, 6))

            # Save history after processing all threads in this cycle
            self.save_conversation_history()

        except Exception as e:
            logger.error(f"An error occurred in the main processing loop: {e}", exc_info=True)

