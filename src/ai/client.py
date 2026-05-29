from typing import Dict, Any

from groq import Groq
from loguru import logger

from src.config import settings


class GroqAIClient:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    async def get_music_recommendation_prompt(self, user_input: str) -> Dict[str, Any]:
        logger.info(f"Generating music recommendation prompt for: {user_input}")
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a music recommendation AI. Analyze the user\'s request for music style, mood, genre, "
                            "and tempo. Extract keywords that can be used for a YouTube music search. "
                            "Respond with a JSON object containing \"mood\", \"genre\", \"tempo\", and \"keywords\". "
                            "If a category is not explicitly mentioned, infer it or leave it as an empty string. "
                            "Keywords should be a comma-separated string suitable for YouTube search. "
                            "Example: {\"mood\": \"energetic\", \"genre\": \"EDM\", \"tempo\": \"fast\", \"keywords\": \"energetic EDM workout music\"}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_input,
                    },
                ],
                model="llama3-8b-8192",  # Or another suitable Groq model
                temperature=0.7,
                max_tokens=256,
                response_format={"type": "json_object"},
            )
            response_content = chat_completion.choices[0].message.content
            import json
            return json.loads(response_content)
        except Exception as e:
            logger.error(f"Groq AI music recommendation failed for \'{user_input}\': {e}")
            return {"mood": "", "genre": "", "tempo": "", "keywords": user_input}


groq_ai_client = GroqAIClient()
