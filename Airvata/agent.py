from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool
from google.adk.llms import GeminiConfiguration
import os

class InstagramTool(BaseTool):
    """Custom tool for Instagram DM operations"""
    name = "instagram_dm_sender"
    description = "Sends responses to Instagram Direct Messages"

    def execute(self, thread_id: str, message: str) -> bool:
        # Implementation would interface with Instagrapi
        
        return True

class ADKInstagramAgent:
    def __init__(self):
        self.agent = LlmAgent(
            name="instagram_dm_responder",
            llm_configuration=GeminiConfiguration(
                model_name="gemini-2.0-flash-exp",
                api_key=os.getenv("GOOGLE_API_KEY")
            ),
            system_instruction="""
            You are an Instagram assistant for a personal account. 
            Your responses must be friendly, concise (under 200 characters), 
            and maintain brand voice. Use emojis as you wish.
            """,
            tools=[InstagramTool()],
            config_path="adk_config.yaml"
        )

    def generate_response(self, message: str, context: dict) -> str:
        response = self.agent.process(
            input_text=message,
            context=context,
            runtime_parameters={
                'max_tokens': 150,
                'temperature': 0.7
            }
        )
        return response.output_text
