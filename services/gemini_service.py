"""
Gemini service for generating Game of Thrones lore scripts (Free Alternative)
"""

import json
import logging
import os
from typing import Dict, List, Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for generating Game of Thrones content using Google Gemini (Free)"""
    
    def __init__(self, config):
        self.config = config
        # Gemini 2.5 Flash is free with generous limits
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # For now, use a fallback approach if no key is provided
            logger.warning("No GEMINI_API_KEY found, service will be limited")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
    
    async def generate_got_script(self, topic: str) -> Optional[Dict[str, str]]:
        """
        Generate a Game of Thrones lore script based on the given topic
        
        Args:
            topic: The Game of Thrones topic to create content about
            
        Returns:
            Dictionary containing script, title, description, and keywords
        """
        try:
            if not self.client:
                # Fallback to a basic template if no API key
                return self._generate_fallback_script(topic)
            
            prompt = self._create_got_prompt(topic)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if not response.text:
                logger.error("Empty response from Gemini")
                return self._generate_fallback_script(topic)
            
            result = json.loads(response.text)
            
            # Validate required fields
            required_fields = ['script', 'title', 'description', 'keywords']
            if not all(field in result for field in required_fields):
                logger.error("Gemini response missing required fields")
                return self._generate_fallback_script(topic)
            
            # Ensure script is appropriate length
            word_count = len(result['script'].split())
            if word_count > self.config.max_script_length:
                logger.warning(f"Script too long ({word_count} words), truncating...")
                words = result['script'].split()[:self.config.max_script_length]
                result['script'] = ' '.join(words)
            
            logger.info(f"Generated script for topic: {topic}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating script with Gemini: {e}")
            return self._generate_fallback_script(topic)
    
    def _generate_fallback_script(self, topic: str) -> Dict[str, str]:
        """Generate a basic script template when API is unavailable"""
        
        # Create a dramatic script based on the topic
        topic_lower = topic.lower()
        
        if "jon snow" in topic_lower and "death" in topic_lower:
            script = """What if I told you Jon Snow's resurrection was planned from the very beginning? 
            Deep in the crypts of Winterfell lies a secret that the Starks have guarded for centuries. 
            The ancient Kings of Winter knew something about death that even the maesters never discovered. 
            When Jon Snow fell at the Wall, bleeding out in the snow, it wasn't just his watch that ended. 
            The old magic that flows through Stark blood began to awaken. 
            The same magic that built the Wall, that bound the White Walkers, that connected the Starks to their direwolves. 
            Melisandre didn't bring Jon back through the Lord of Light's power alone. 
            She tapped into something far older, something that runs in the very stones of Winterfell. 
            The truth about Jon Snow's return changes everything we thought we knew about the Stark legacy."""
            
            title = "The REAL Reason Jon Snow Returned From Death"
            keywords = ["jon snow", "winterfell", "stark", "resurrection", "wall", "direwolf"]
            
        elif "night king" in topic_lower:
            script = """What if I told you the Night King wasn't the first of his kind? 
            Hidden in the ancient texts of Old Valyria lies a terrifying truth about the Long Night. 
            The Children of the Forest didn't create just one Night King - they created twelve. 
            Each one bound to a different element of ice and darkness. 
            The Night King we saw was merely the first to break free from his prison beyond the Wall. 
            But the others still wait, frozen in time, in places across Essos and beyond. 
            The Dragon Queen's conquest of Slaver's Bay unknowingly awakened something ancient in the ruins of Old Ghis. 
            The true war against the dead hasn't even begun. 
            What we witnessed at Winterfell was just the beginning of a nightmare that spans continents."""
            
            title = "There Were 12 Night Kings - Here's The Proof"
            keywords = ["night king", "white walkers", "children of the forest", "valyria", "long night"]
            
        else:
            # Generic Game of Thrones template
            script = f"""What if I told you the truth about {topic} changes everything we know about Westeros? 
            Deep in the archives of the Citadel lies a forbidden text that reveals secrets the maesters never wanted known. 
            This ancient knowledge connects the Targaryens, the Starks, and the very foundation of the Seven Kingdoms. 
            The game of thrones was never about who sits on the Iron Throne. 
            It was about controlling a power that could reshape the world itself. 
            From the Wall to Dorne, from the Iron Islands to Asshai, every major house guards a piece of this puzzle. 
            The dragons, the direwolves, the ancient magic - it all connects to one terrible truth. 
            A truth that would make even the bravest knights of Westeros tremble in fear. 
            The real war was never between the living and the dead - it was between those who know and those who remain ignorant."""
            
            title = f"The Hidden Truth About {topic.title()}"
            keywords = ["westeros", "game of thrones", "targaryen", "stark", "citadel", "dragon"]
        
        description = f"🐉 Discover the shocking truth about {topic} that changes everything! This Game of Thrones theory will blow your mind. #GameOfThrones #GoT #HouseOfTheDragon #Westeros #Theory"
        
        return {
            "script": script,
            "title": title,
            "description": description,
            "keywords": keywords
        }
    
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
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
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
        if not self.client:
            return script  # Return original if no API
            
        try:
            prompt = f"""
            Enhance this Game of Thrones script for text-to-speech narration:
            
            "{script}"
            
            Make these improvements:
            - Add dramatic pauses with commas and periods
            - Replace difficult pronunciations with phonetic alternatives
            - Add emphasis markers for key dramatic moments
            - Ensure smooth flow for voice narration
            - Keep the same meaning and impact
            
            Return only the enhanced script text.
            """
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text.strip() if response.text else script
            
        except Exception as e:
            logger.error(f"Error enhancing script: {e}")
            return script
    
    def validate_got_content(self, content: str) -> bool:
        """
        Validate that content is appropriate Game of Thrones lore
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid GoT lore
        """
        got_keywords = [
            'westeros', 'essos', 'targaryen', 'stark', 'lannister', 'baratheon',
            'dragon', 'direwolf', 'iron throne', 'wall', 'winterfell', 'king\'s landing',
            'jon snow', 'daenerys', 'tyrion', 'arya', 'sansa', 'night king',
            'white walker', 'valyrian', 'dothraki', 'braavos', 'oldtown'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in got_keywords)