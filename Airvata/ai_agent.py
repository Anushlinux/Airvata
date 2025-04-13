import os
import logging
import time
from dotenv import load_dotenv
import google.generativeai as genai
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()
logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        try:
            # Create agent definition
            self.agent = LlmAgent(
                model="gemini-2.0-flash-exp",
                name="instagram_assistant",
                description="Instagram DM assistant",
                instruction="""
                You are an Instagram assistant. Your task is to respond to direct messages
                in a friendly, helpful manner. Keep responses concise (1-3 sentences).
                Do not explicitly mention you are an AI unless directly asked.
                If you receive spam or inappropriate content, respond with "[IGNORE]".
                """
            )
            
            # Setup session service and runner
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.agent,
                app_name="instagram_dm_bot",
                session_service=self.session_service
            )
            logger.info("AI Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Agent: {e}")
            raise
    
    def ensure_session(self, thread_id):
        """Ensure a session exists for the thread"""
        session_id = str(thread_id)
        try:
            # Check if session already exists
            exists = False
            try:
                # Try to get session info (will raise exception if not found)
                # Use session_service to get session info
                self.session_service.get_session_info("instagram_user", session_id)
                exists = True
                logger.info(f"Session {session_id} already exists")
            except Exception:
                logger.info(f"Session {session_id} not found, creating new one")

            # Create session only if it doesn't exist
            if not exists:
                # Use session_service to create the session
                self.session_service.create_session(
                    user_id="instagram_user",
                    session_id=session_id
                )
                logger.info(f"Session {session_id} created successfully")

            return True
        except Exception as e:
            logger.error(f"Failed to ensure session {session_id}: {str(e)}")
            # Don't silently fail - return False if session couldn't be created/verified
            return False
    
    def generate_response(self, thread_id, message_text, context=""):
        """Generate a response using ADK"""
        logger.info(f"Generating response for message: {message_text}")
        
        if not message_text or message_text.strip() == "":
            logger.warning("Empty message text provided")
            return None
        
        # Ensure thread_id is a string for session ID
        session_id = str(thread_id)
        
        retry_count = 0
        max_retries = 3
        session_ready = False
        
        while retry_count < max_retries and not session_ready:
            if self.ensure_session(session_id):
                try:
                    # Verify session exists before proceeding
                    self.runner.get_session_info("instagram_user", session_id)
                    session_ready = True
                    logger.info(f"Session {session_id} verified and ready")
                except Exception as e:
                    logger.warning(f"Session verification failed on attempt {retry_count+1}: {e}")
                    retry_count += 1
                    time.sleep(0.5)  # Small delay between retries
            else:
                retry_count += 1
                time.sleep(0.5)
        
        # Make sure the session exists - abort if it can't be created
        if not session_ready:
            logger.error(f"Cannot generate response: Failed to ensure session {session_id} is ready after {max_retries} retries.")
            return "I'm having trouble processing your message right now. I'll get back to you soon."
        
        try:
            # Prepare input with context and new message
            full_input = f"Previous messages:\n{context}\n\nNew message: {message_text or ''}" 
            # Create content object for ADK
            content = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=full_input)]
            )
            
            # Get response using the runner
            response_text = None
            events = self.runner.run(
                user_id="instagram_user",
                session_id=session_id,
                new_message=content
            )
            
            # Process events to get final response
            for event in events:
                if hasattr(event, "is_final_response") and event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text.strip()
                        break
            
            # Check if agent wants to ignore the message
            if response_text == "[IGNORE]":
                logger.info("Agent decided to ignore the message")
                return None
                
            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble processing your message right now. I'll get back to you soon."
