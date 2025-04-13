# Airvata

Automated replies to your `nalle` friends who sends you 100 reels everyday and expect reaction to each of them ;)

## Description

This bot logs into an Instagram account, periodically checks for unread DMs, processes new messages using an AI agent (powered by Google's Gemini model via the Agent Development Kit - ADK), and sends back generated replies. It maintains conversation history and tracks processed messages to avoid duplicates.

## Features

*   Logs into Instagram using session persistence ([`Airvata/instagram_client.py`](Airvata/instagram_client.py)).
*   Fetches unread Instagram DM threads ([`Airvata/instagram_client.py`](Airvata/instagram_client.py)).
*   Processes new messages, ignoring empty or already processed ones ([`Airvata/dm_handler.py`](Airvata/dm_handler.py)).
*   Maintains conversation history per thread ([`Airvata/conversation_history.json`](Airvata/conversation_history.json), [`Airvata/dm_handler.py`](Airvata/dm_handler.py)).
*   Uses Google's Generative AI (Gemini via ADK) to generate context-aware responses ([`Airvata/ai_agent.py`](../../../../../C:/Users/anush/Documents/unemployed-9000/Airvata/ai_agent.py)).
*   Handles ADK sessions for conversational context ([`Airvata/ai_agent.py`](../../../../../C:/Users/anush/Documents/unemployed-9000/Airvata/ai_agent.py)).
*   Sends replies back to the Instagram DM thread ([`Airvata/instagram_client.py`](Airvata/instagram_client.py)).
*   Saves processed message IDs to prevent re-processing ([`Airvata/processed_ids.json`](Airvata/processed_ids.json), [`Airvata/dm_handler.py`](Airvata/dm_handler.py)).
*   Configurable check interval for new messages.
*   Logs activity to `Airvata/instagram_bot.log`.

## Technology Stack

*   **Python 3**
*   **instagrapi:** For interacting with the private Instagram API.
*   **google-generativeai & google-adk:** For AI response generation using Gemini models.
*   **python-dotenv:** For managing environment variables.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory (it's ignored by git) with the following content:
    ```env
    INSTAGRAM_USERNAME="your_instagram_username"
    INSTAGRAM_PASSWORD="your_instagram_password"
    GEMINI_API_KEY="your_google_gemini_api_key"
    CHECK_INTERVAL_SECONDS="60" # Optional: defaults to 60 seconds
    ```
5.  **Configure ADK Agent (Optional):**
    Modify the agent's behavior, model, or tools in [`Airvata/adk_config.yaml`](Airvata/adk_config.yaml).

## Usage

Run the main script to start the bot:

```bash
python Airvata/main.py
