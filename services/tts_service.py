"""
Text-to-Speech service using Google TTS
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from gtts import gTTS
import tempfile

logger = logging.getLogger(__name__)

class TTSService:
    """Service for converting text to speech using Google TTS"""
    
    def __init__(self, config):
        self.config = config
        self.language = 'en'
        self.slow = False  # Normal speed for better engagement
    
    async def text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech and save as audio file
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to the generated audio file, or None if failed
        """
        try:
            # Clean and prepare text for TTS
            cleaned_text = self._prepare_text_for_tts(text)
            
            # Generate unique filename
            audio_filename = f"narration_{hash(cleaned_text) % 100000}.mp3"
            audio_path = self.config.temp_dir / audio_filename
            
            # Run TTS in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, self._generate_speech, cleaned_text, str(audio_path)
            )
            
            # Verify file was created
            if audio_path.exists() and audio_path.stat().st_size > 0:
                logger.info(f"Generated TTS audio: {audio_filename}")
                return str(audio_path)
            else:
                logger.error("TTS file was not created or is empty")
                return None
                
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
            return None
    
    def _generate_speech(self, text: str, output_path: str):
        """
        Generate speech using gTTS (runs in executor)
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
        """
        try:
            # Create TTS object with optimal settings for narration
            tts = gTTS(
                text=text,
                lang=self.language,
                slow=self.slow,
                lang_check=True
            )
            
            # Save to file
            tts.save(output_path)
            logger.info(f"TTS generated successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            raise
    
    def _prepare_text_for_tts(self, text: str) -> str:
        """
        Prepare text for optimal TTS pronunciation with dramatic pacing
        
        Args:
            text: Original text
            
        Returns:
            Cleaned text optimized for TTS with dramatic emphasis
        """
        # Remove markdown formatting
        text = text.replace('**', '').replace('*', '')
        text = text.replace('_', '').replace('`', '')
        
        # Add dramatic pauses and emphasis
        text = text.replace('.', '... ')  # Longer pauses for drama
        text = text.replace('!', '! ')
        text = text.replace('?', '?... ')  # Pause after questions for impact
        text = text.replace(',', '... ')  # Slight pauses for emphasis
        text = text.replace(';', '... ')
        text = text.replace(':', ':... ')
        
        # Add emphasis markers for dramatic words
        dramatic_words = [
            'death', 'murder', 'betrayal', 'secret', 'hidden', 'revealed', 
            'shocking', 'truth', 'lie', 'power', 'throne', 'king', 'queen',
            'dragon', 'war', 'battle', 'blood', 'fire', 'ice', 'prophecy',
            'destiny', 'fate', 'revenge', 'love', 'hate', 'honor', 'betrayed'
        ]
        
        for word in dramatic_words:
            text = text.replace(f' {word} ', f' {word.upper()} ')
            text = text.replace(f' {word.capitalize()} ', f' {word.upper()} ')
        
        # Replace common Game of Thrones names with phonetic versions
        pronunciations = {
            'Daenerys': 'Dah-NAIR-iss',
            'Targaryen': 'TAR-GAIR-ee-en',
            'Valyrian': 'Val-EAR-ee-an',
            'Dothraki': 'DOTH-rah-kee',
            'Braavos': 'BRAH-vos',
            'Tyrion': 'TEER-ee-on',
            'Jaime': 'HIGH-me',
            'Cersei': 'SER-say',
            'Aegon': 'AY-gon',
            'Rhaegar': 'RAY-gar',
            'Lyanna': 'lee-ANN-ah',
            'Joffrey': 'JOFF-ree',
            'Stannis': 'STAN-iss',
            'Melisandre': 'mel-ih-SAN-dray',
            'Missandei': 'miss-an-DAY',
            'Varys': 'VAIR-iss',
            'Petyr': 'PEE-tur',
            'Catelyn': 'CAT-lin',
            'Sansa': 'SAN-sah',
            'Arya': 'ARE-yah',
            'Robb': 'Rob',
            'Theon': 'THEE-on',
            'Ygritte': 'ee-GRIT',
            'Samwell': 'SAM-well',
            'Gendry': 'GEN-dree',
            'Sandor': 'SAN-door',
            'Gregor': 'GREG-or',
            'Westeros': 'WEST-er-os',
            'Essos': 'ESS-os',
            'Winterfell': 'WIN-ter-fell',
            'Dragonstone': 'DRAG-on-stone'
        }
        
        # Apply pronunciations
        for name, pronunciation in pronunciations.items():
            text = text.replace(name, pronunciation)
        
        # Add strategic pauses at the beginning and key moments
        if text.startswith(('What if', 'Imagine', 'Picture this')):
            text = text.replace('What if', 'What if... ')
            text = text.replace('Imagine', 'Imagine... ')
            text = text.replace('Picture this', 'Picture this... ')
        
        # Clean up extra spaces but preserve strategic pauses
        text = ' '.join(text.split())
        
        return text
    
    async def get_audio_duration(self, audio_path: str) -> Optional[float]:
        """
        Get the duration of an audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or None if failed
        """
        try:
            import mutagen
            from mutagen.mp3 import MP3
            
            def _get_duration():
                audio = MP3(audio_path)
                return audio.info.length
            
            duration = await asyncio.get_event_loop().run_in_executor(
                None, _get_duration
            )
            
            logger.info(f"Audio duration: {duration:.2f} seconds")
            return duration
            
        except ImportError:
            logger.warning("mutagen not available, cannot get audio duration")
            return None
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None
    
    def cleanup_audio(self, audio_path: str):
        """
        Clean up audio file
        
        Args:
            audio_path: Path to audio file to remove
        """
        try:
            Path(audio_path).unlink(missing_ok=True)
            logger.info(f"Cleaned up audio: {audio_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup audio {audio_path}: {e}")
