import time
import logging
import os
from dotenv import load_dotenv
from instagram_client import InstagramClient
from ai_agent import AIAgent
from dm_handler import MessageHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("instagram_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    load_dotenv()
    logger.info("Starting Instagram DM AI bot")
    
    try:
        # Initialize Instagram client
        instagram_client = InstagramClient()
        if not instagram_client.login():
            logger.error("Failed to login to Instagram. Exiting.")
            return
        
        # Initialize AI agent
        ai_agent = AIAgent()
        
        # Initialize message handler
        message_handler = MessageHandler(instagram_client, ai_agent)
        
        # Main loop
        check_interval = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
        logger.info(f"Bot started. Checking for messages every {check_interval} seconds")
        
        while True:
            try:
                message_handler.process_messages()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            # Wait before checking again
            logger.info(f"Waiting {check_interval} seconds before next check")
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
    finally:
        # Ensure state is saved on exit
        if 'message_handler' in locals():
            message_handler.save_state()
        logger.info("Bot stopped")

if __name__ == "__main__":
    main()
