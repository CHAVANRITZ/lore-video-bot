"""
OpenAI service for generating Game of Thrones lore scripts
"""

import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for generating Game of Thrones content using OpenAI"""
    
    def __init__(self, config):
        self.config = config
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = "gpt-4o"
    
    async def generate_got_script(self, topic: str) -> Optional[Dict[str, str]]:
        """
        Generate a Game of Thrones lore script based on the given topic
        
        Args:
            topic: The Game of Thrones topic to create content about
            
        Returns:
            Dictionary containing script, title, description, and keywords
        """
        try:
            prompt = self._create_got_prompt(topic)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Game of Thrones lore expert and engaging storyteller. "
                        "Create compelling, accurate content that captures the epic nature of the series. "
                        "Always respond with valid JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.8
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['script', 'title', 'description', 'keywords']
            if not all(field in result for field in required_fields):
                logger.error("OpenAI response missing required fields")
                return None
            
            # Ensure script is appropriate length
            word_count = len(result['script'].split())
            if word_count > self.config.max_script_length:
                logger.warning(f"Script too long ({word_count} words), truncating...")
                words = result['script'].split()[:self.config.max_script_length]
                result['script'] = ' '.join(words)
            
            logger.info(f"Generated script for topic: {topic}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None
    
    def _create_got_prompt(self, topic: str) -> str:
        """Create a detailed prompt for Game of Thrones content generation"""
        
        return f"""
        Create an engaging Game of Thrones lore video script about: "{topic}"

        Requirements:
        - Script should be exactly 45-55 seconds when spoken (approximately 450-500 words)
        - START with a POWERFUL HOOK that grabs attention immediately
        - Use dramatic, cinematic language with short punchy sentences
        - Focus on canon lore from the books and show
        - Build suspense and mystery throughout
        - Include specific character names, locations, and events
        - End with a compelling cliffhanger or shocking revelation
        - Make it perfect for YouTube Shorts audience (high engagement)

        HOOK EXAMPLES:
        - "What if I told you Jon Snow's death was planned all along?"
        - "This one secret about Daenerys changes everything..."
        - "The Night King had a plan no one saw coming..."

        Provide your response as JSON with these exact fields:
        {{
            "title": "Engaging clickbait title (60 characters max)",
            "script": "The complete narration script with strong hook",
            "description": "YouTube description with hashtags (500 characters max)",
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"] (for image search)
        }}

        Make the script dramatic and captivating, like a movie trailer narrator.
        Use cliffhangers, mysteries, and "what if" scenarios.
        Include specific Game of Thrones terminology and references that fans will appreciate.
        
        Keywords should be visual terms that will help find relevant medieval/fantasy images:
        - Character names
        - Locations (Winterfell, King's Landing, etc.)
        - Themes (dragons, ice, fire, crown, sword, etc.)
        - Atmospheric terms (castle, throne, battle, etc.)
        """
    
    async def enhance_script_for_voice(self, script: str) -> str:
        """
        Enhance script for better text-to-speech pronunciation
        
        Args:
            script: Original script text
            
        Returns:
            Enhanced script with pronunciation improvements
        """
        try:
            prompt = f"""
            Enhance this Game of Thrones script for text-to-speech narration:
            
            "{script}"
            
            Rules:
            - Add pronunciation guides for difficult names (e.g., "Daenerys (dah-NAIR-iss)")
            - Add natural pauses with punctuation
            - Ensure smooth flow for speech synthesis
            - Keep the same content and length
            - Don't change the story or facts
            
            Return only the enhanced script text, no additional formatting.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            enhanced_script = response.choices[0].message.content.strip()
            logger.info("Enhanced script for TTS")
            return enhanced_script
            
        except Exception as e:
            logger.warning(f"Failed to enhance script for voice: {e}")
            return script  # Return original if enhancement fails
    
    def validate_got_content(self, content: str) -> bool:
        """
        Validate that content is appropriate Game of Thrones lore
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid GoT lore
        """
        got_keywords = [
            'westeros', 'essos', 'stark', 'lannister', 'targaryen', 'baratheon',
            'dragon', 'iron throne', 'winter', 'king\'s landing', 'winterfell',
            'jon snow', 'daenerys', 'tyrion', 'arya', 'sansa', 'bran',
            'night king', 'white walkers', 'valyrian', 'dothraki', 'braavos'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in got_keywords)
