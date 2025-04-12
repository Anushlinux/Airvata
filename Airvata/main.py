from instagrapi import Client
import os
from dotenv import load_dotenv
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

def test_instagrapi():
    # Create client
    cl = Client()
    
    # Login
    cl.login(os.getenv("INSTAGRAM_USERNAME"), os.getenv("INSTAGRAM_PASSWORD"))
    
    # Get user ID
    username = os.getenv("INSTAGRAM_USERNAME")
    user_id = cl.user_id_from_username(username)
    print(f"User ID: {user_id}")
    
    # Get a few media items using the private API (which works based on your logs)
    medias = cl.user_medias_v1(user_id, 3)
    
    # Print basic info about the media
    print(f"Successfully retrieved {len(medias)} media items")
    for media in medias:
        print(f"Media ID: {media.id}, Type: {media.media_type}")
    
    return True

if __name__ == "__main__":
    if test_instagrapi():
        print("✅ instagrapi is working correctly!")