"""
Gemini service for generating Game of Thrones lore scripts (Free Alternative)
"""

import os
import json
import logging
from typing import Dict, List, Optional
import google.generativeai as genai  # ✅ Official import

from google.generativeai.types import GenerateContentConfig

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for generating Game of Thrones content using Google Gemini (Free)"""

    def __init__(self, config):
        self.config = config
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("No GEMINI_API_KEY found, service will be limited")
            self.client = None
        else:
            genai.configure(api_key=api_key)
            self.client = genai
        self.model = "gemini-1.5-flash"  # or "gemini-pro" if needed

    async def generate_got_script(self,
                                  topic: str) -> Optional[Dict[str, str]]:
        try:
            if not self.client:
                return self._generate_fallback_script(topic)

            prompt = self._create_got_prompt(topic)

            response = self.client.GenerativeModel(
                self.model).generate_content(
                    prompt,
                    generation_config=GenerateContentConfig(
                        response_mime_type="application/json"))

            if not response.text:
                logger.error("Empty response from Gemini")
                return self._generate_fallback_script(topic)

            result = json.loads(response.text)
            required_fields = ['script', 'title', 'description', 'keywords']
            if not all(field in result for field in required_fields):
                logger.error("Gemini response missing required fields")
                return self._generate_fallback_script(topic)

            word_count = len(result['script'].split())
            if word_count > self.config.max_script_length:
                logger.warning(
                    f"Script too long ({word_count} words), truncating...")
                result['script'] = ' '.join(
                    result['script'].split()[:self.config.max_script_length])

            logger.info(f"Generated script for topic: {topic}")
            return result

        except Exception as e:
            logger.error(f"Error generating script with Gemini: {e}")
            return self._generate_fallback_script(topic)

    def _generate_fallback_script(self, topic: str) -> Dict[str, str]:
        topic_lower = topic.lower()

        if "jon snow" in topic_lower and "death" in topic_lower:
            script = """What if I told you Jon Snow's resurrection was planned from the very beginning?..."""
            title = "The REAL Reason Jon Snow Returned From Death"
            keywords = [
                "jon snow", "winterfell", "stark", "resurrection", "wall",
                "direwolf"
            ]

        elif "night king" in topic_lower:
            script = """What if I told you the Night King wasn't the first of his kind?..."""
            title = "There Were 12 Night Kings - Here's The Proof"
            keywords = [
                "night king", "white walkers", "children of the forest",
                "valyria", "long night"
            ]

        else:
            script = f"""What if I told you the truth about {topic} changes everything we know about Westeros?..."""
            title = f"The Hidden Truth About {topic.title()}"
            keywords = [
                "westeros", "game of thrones", "targaryen", "stark", "citadel",
                "dragon"
            ]

        description = f"🐉 Discover the shocking truth about {topic} that changes everything! This Game of Thrones theory will blow your mind. #GameOfThrones #GoT #HouseOfTheDragon #Westeros #Theory"

        return {
            "script": script,
            "title": title,
            "description": description,
            "keywords": keywords
        }

    def _create_got_prompt(self, topic: str) -> str:
        return f"""
        Create an engaging Game of Thrones lore video script about: "{topic}"
        Requirements:
        - Script should be 45–55 seconds (≈ 450-500 words)
        - Start with a strong hook
        - Use dramatic, cinematic tone
        - Include real book/show lore, specific names, places
        - End with a cliffhanger or twist
        Return JSON with fields: title, script, description, keywords
        """

    async def enhance_script_for_voice(self, script: str) -> str:
        if not self.client:
            return script

        try:
            prompt = f"""
            Enhance this script for dramatic text-to-speech:
            "{script}"
            Add pauses, simplify pronunciations, and ensure flow.
            """
            response = self.client.GenerativeModel(
                self.model).generate_content(prompt)
            return response.text.strip() if response.text else script
        except Exception as e:
            logger.error(f"Error enhancing script: {e}")
            return script

    def validate_got_content(self, content: str) -> bool:
        got_keywords = [
            'westeros', 'essos', 'targaryen', 'stark', 'lannister',
            'baratheon', 'dragon', 'direwolf', 'iron throne', 'wall',
            'winterfell', "king's landing", 'jon snow', 'daenerys', 'tyrion',
            'arya', 'sansa', 'night king', 'white walker', 'valyrian',
            'dothraki', 'braavos', 'oldtown'
        ]
        return any(k in content.lower() for k in got_keywords)
