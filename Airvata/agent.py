# ai_agent.py
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.adk.agents import LlmAgent

load_dotenv()
logger = logging.getLogger(__name__)

class ADKAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure genai primarily for validation/direct use if ADK fails
        genai.configure(api_key=self.api_key)

        # Define the ADK Agent
        try:
            self.agent = LlmAgent(
                # Specify the model directly (Check ADK docs for latest valid names)
                model="gemini-2.0-flash-exp",
                name="instagram_responder_agent",
                description="An AI agent that responds to Instagram direct messages.",
                instruction="""
                You are a helpful and friendly assistant managing an Instagram account.
                Analyze the incoming message based on the provided conversation history (if any).
                Generate a concise, relevant, and engaging reply suitable for Instagram DMs.
                Keep the tone positive and conversational. Use emojis appropriately but sparingly.
                Do NOT explicitly state you are an AI.
                If the message is spam, irrelevant, or abusive, output only the text: [IGNORE]
                If you cannot help, politely state you will forward the message to a human.
                Base your response ONLY on the provided context and the new message.
                """,
                # No tools needed if the agent's only job is to generate reply text
                # tools=[]
            )
            logger.info("ADK LlmAgent initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ADK Agent: {e}", exc_info=True)
            raise

    def generate_response(self, message_text: str, conversation_context: list[str]) -> str:
        """
        Generates a response using the ADK agent.
        Args:
            message_text: The new incoming message text.
            conversation_context: A list of strings representing previous turns.
        Returns:
            The generated response text, or None if an error occurs or message should be ignored.
        """
        logger.info("Generating response using ADK agent...")
        context_string = "\n".join(conversation_context) if conversation_context else "No previous conversation."
        full_input = f"Conversation History:\n{context_string}\n\nNew Message: {message_text}"

        try:
            # Use agent.process() for ADK's managed interaction
            response = self.agent.process(input_text=full_input) # Pass combined history + new message
            generated_text = response.output_text.strip()
            logger.info(f"ADK Agent generated response: '{generated_text}'")

            if generated_text == "[IGNORE]":
                logger.info("Agent decided to ignore the message.")
                return None # Signal to ignore

            return generated_text

        except Exception as e:
            logger.error(f"Error during ADK agent processing: {e}", exc_info=True)
            # Fallback or default response
            return "Sorry, I encountered a technical issue. I'll get back to you soon!"

