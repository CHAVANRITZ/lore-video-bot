"""
Video creation service using FFmpeg
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class VideoService:
    """Service for creating vertical videos from images and audio"""
    
    def __init__(self, config):
        self.config = config
        self.output_width = config.video_width
        self.output_height = config.video_height
        self.fps = 30
    
    async def create_vertical_video(
        self, 
        script_data: Dict[str, str], 
        image_paths: List[str], 
        audio_path: str
    ) -> Optional[str]:
        """
        Create a vertical video from images and audio
        
        Args:
            script_data: Dictionary containing title and other metadata
            image_paths: List of paths to images
            audio_path: Path to audio file
            
        Returns:
            Path to created video file, or None if failed
        """
        try:
            if len(image_paths) < 3:
                logger.error("Insufficient images for video creation")
                return None
            
            # Get audio duration
            audio_duration = await self._get_audio_duration(audio_path)
            if not audio_duration:
                logger.error("Could not determine audio duration")
                return None
            
            # Calculate timing for images
            image_duration = audio_duration / len(image_paths)
            
            # Generate output filename
            safe_title = "".join(c for c in script_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            video_filename = f"got_video_{safe_title}_{hash(audio_path) % 10000}.mp4"
            output_path = self.config.temp_dir / video_filename
            
            # Create video
            success = await self._create_video_with_ffmpeg(
                image_paths, audio_path, str(output_path), image_duration
            )
            
            if success and output_path.exists():
                logger.info(f"Video created successfully: {video_filename}")
                return str(output_path)
            else:
                logger.error("Video creation failed")
                return None
                
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return None
    
    async def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Get audio duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                duration = float(stdout.decode().strip())
                logger.info(f"Audio duration: {duration:.2f} seconds")
                return duration
            else:
                logger.error(f"ffprobe error: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None
    
    async def _create_video_with_ffmpeg(
        self, 
        image_paths: List[str], 
        audio_path: str, 
        output_path: str,
        image_duration: float
    ) -> bool:
        """
        Create video using FFmpeg with smooth transitions
        
        Args:
            image_paths: List of image file paths
            audio_path: Path to audio file
            output_path: Output video path
            image_duration: Duration to show each image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filter complex for smooth image transitions with subtitles
            filter_complex = self._build_filter_complex(image_paths, image_duration, script_data['script'])
            
            # FFmpeg command for vertical video with transitions
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-loglevel', 'warning',  # Reduce verbose output
            ]
            
            # Add input images
            for image_path in image_paths:
                cmd.extend(['-loop', '1', '-t', str(image_duration + 1), '-i', image_path])
            
            # Add audio input
            cmd.extend(['-i', audio_path])
            
            # Add filter complex
            cmd.extend(['-filter_complex', filter_complex])
            
            # Output settings for vertical video
            cmd.extend([
                '-map', f'[output]',  # Use the filtered video
                '-map', f'{len(image_paths)}:a',  # Use the audio
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-b:v', '2M',  # Video bitrate
                '-b:a', '128k',  # Audio bitrate
                '-r', str(self.fps),  # Frame rate
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-movflags', '+faststart',  # Optimize for streaming
                '-shortest',  # End when shortest input ends
                output_path
            ])
            
            logger.info("Starting video creation with FFmpeg...")
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("FFmpeg completed successfully")
                return True
            else:
                logger.error(f"FFmpeg failed with return code {process.returncode}")
                logger.error(f"FFmpeg stderr: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error running FFmpeg: {e}")
            return False
    
    def _build_filter_complex(self, image_paths: List[str], image_duration: float, script_text: str) -> str:
        """
        Build FFmpeg filter complex for cinematic image animations with burned-in subtitles
        
        Args:
            image_paths: List of image paths
            image_duration: Duration for each image
            script_text: Script text for subtitle extraction
            
        Returns:
            FFmpeg filter complex string
        """
        filters = []
        
        # Scale, crop and add cinematic animations to each image
        for i in range(len(image_paths)):
            # Determine animation type based on image position
            if i % 3 == 0:
                # Ken Burns zoom in effect
                animation = (
                    f"[{i}:v]scale={self.output_width * 2}:{self.output_height * 2}:"
                    f"force_original_aspect_ratio=increase,"
                    f"crop={self.output_width}:{self.output_height},"
                    f"zoompan=z='min(zoom+0.0015,1.5)':d={int(self.fps * image_duration)}:"
                    f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.output_width}x{self.output_height},"
                    f"setpts=PTS-STARTPTS[v{i}]"
                )
            elif i % 3 == 1:
                # Slow pan right effect
                animation = (
                    f"[{i}:v]scale={self.output_width * 1.2}:{self.output_height * 1.2}:"
                    f"force_original_aspect_ratio=increase,"
                    f"crop={self.output_width}:{self.output_height},"
                    f"zoompan=z='1':d={int(self.fps * image_duration)}:"
                    f"x='if(gte(on,1),x+2,0)':y='ih/2-(ih/zoom/2)':"
                    f"s={self.output_width}x{self.output_height},"
                    f"setpts=PTS-STARTPTS[v{i}]"
                )
            else:
                # Slow zoom out effect
                animation = (
                    f"[{i}:v]scale={self.output_width * 1.5}:{self.output_height * 1.5}:"
                    f"force_original_aspect_ratio=increase,"
                    f"crop={self.output_width}:{self.output_height},"
                    f"zoompan=z='min(zoom-0.001,1.0)':d={int(self.fps * image_duration)}:"
                    f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.output_width}x{self.output_height},"
                    f"setpts=PTS-STARTPTS[v{i}]"
                )
            
            filters.append(animation)
        
        # Create dramatic crossfade transitions between images
        if len(image_paths) == 1:
            # Single image case with fade in/out
            base_video = f"{filters[0]};[v0]fade=t=in:st=0:d=0.5,fade=t=out:st={image_duration-0.5}:d=0.5[base]"
        else:
            # Multiple images with cinematic transitions
            transition_duration = 0.8  # Longer crossfade for dramatic effect
            
            # Start with first image
            current_stream = "v0"
            
            for i in range(1, len(image_paths)):
                if i == 1:
                    # First transition with fade
                    filters.append(
                        f"[{current_stream}][v{i}]xfade=transition=fadeblack:"
                        f"duration={transition_duration}:"
                        f"offset={image_duration - transition_duration}[fade{i}]"
                    )
                    current_stream = f"fade{i}"
                else:
                    # Subsequent transitions alternating effects
                    transition_type = "wiperight" if i % 2 == 0 else "fadeblack"
                    filters.append(
                        f"[{current_stream}][v{i}]xfade=transition={transition_type}:"
                        f"duration={transition_duration}:"
                        f"offset={i * image_duration - transition_duration}[fade{i}]"
                    )
                    current_stream = f"fade{i}"
            
            # Base video with color grading
            base_video = f"[{current_stream}]eq=contrast=1.1:brightness=0.05:saturation=1.2[base]"
            
        # Add burned-in subtitles
        subtitle_text = self._extract_key_phrases(script_text)
        subtitle_filter = self._create_subtitle_filter(subtitle_text, len(image_paths) * image_duration)
        
        # Combine base video with subtitles
        final_filter = f"{base_video};[base]{subtitle_filter}[output]"
        filter_complex = ";".join(filters) + ";" + final_filter
        
        return filter_complex
    
    def _extract_key_phrases(self, script_text: str) -> List[str]:
        """Extract key dramatic phrases from script for subtitles"""
        import re
        
        # Split into sentences and extract impactful phrases
        sentences = re.split(r'[.!?]+', script_text)
        key_phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Skip very short sentences
                # Look for dramatic phrases or convert to upper case for impact
                if any(word in sentence.lower() for word in ['what if', 'secret', 'truth', 'never', 'hidden', 'revealed']):
                    key_phrases.append(sentence.upper())
                elif len(sentence) < 50:  # Short impactful sentences
                    key_phrases.append(sentence.upper())
        
        # Limit to 3-4 key phrases to avoid overcrowding
        return key_phrases[:4]
    
    def _create_subtitle_filter(self, phrases: List[str], total_duration: float) -> str:
        """Create FFmpeg filter for burned-in subtitles like your reference images"""
        if not phrases:
            return ""
        
        # Calculate timing for each phrase
        phrase_duration = total_duration / len(phrases)
        
        # Create subtitle filter with dramatic styling
        subtitle_filters = []
        
        for i, phrase in enumerate(phrases):
            start_time = i * phrase_duration
            end_time = (i + 1) * phrase_duration
            
            # Clean text for FFmpeg
            clean_phrase = phrase.replace("'", "\\'").replace('"', '\\"')
            
            # Create drawtext filter with GoT-style formatting
            subtitle_filter = (
                f"drawtext=text='{clean_phrase}':"
                f"x=(w-text_w)/2:"  # Center horizontally
                f"y=h-150:"  # Position near bottom
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=48:"
                f"fontcolor=white:"
                f"borderw=3:"
                f"bordercolor=black:"
                f"box=1:"
                f"boxcolor=black@0.7:"
                f"boxborderw=10:"
                f"enable='between(t,{start_time},{end_time})'"
            )
            subtitle_filters.append(subtitle_filter)
        
        return ",".join(subtitle_filters)
    
    async def optimize_for_youtube_shorts(self, video_path: str) -> Optional[str]:
        """
        Optimize video specifically for YouTube Shorts
        
        Args:
            video_path: Path to input video
            
        Returns:
            Path to optimized video, or None if failed
        """
        try:
            optimized_filename = f"optimized_{Path(video_path).name}"
            optimized_path = self.config.temp_dir / optimized_filename
            
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',  # Good quality
                '-maxrate', '2.5M',  # YouTube Shorts max bitrate
                '-bufsize', '5M',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',  # Standard audio sample rate
                '-ac', '2',  # Stereo
                '-movflags', '+faststart',
                '-f', 'mp4',
                str(optimized_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Video optimized for YouTube Shorts")
                return str(optimized_path)
            else:
                logger.error(f"Optimization failed: {stderr.decode()}")
                return video_path  # Return original if optimization fails
                
        except Exception as e:
            logger.error(f"Error optimizing video: {e}")
            return video_path  # Return original if optimization fails
    
    def cleanup_video(self, video_path: str):
        """
        Clean up video file
        
        Args:
            video_path: Path to video file to remove
        """
        try:
            Path(video_path).unlink(missing_ok=True)
            logger.info(f"Cleaned up video: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup video {video_path}: {e}")
