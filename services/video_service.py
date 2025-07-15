import asyncio
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VideoService:

    def __init__(self, config):
        self.config = config
        self.output_width = config.video_width
        self.output_height = config.video_height
        self.fps = 30

    async def create_vertical_video(self, script_data: Dict[str, str],
                                    image_paths: List[str],
                                    audio_path: str) -> Optional[str]:
        try:
            if len(image_paths) < 3:
                logger.error("Insufficient images for video creation")
                return None

            audio_duration = await self._get_audio_duration(audio_path)
            if not audio_duration:
                logger.error("Could not determine audio duration")
                return None

            image_duration = audio_duration / len(image_paths)
            safe_title = "".join(
                c for c in script_data['title']
                if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(
                    " ", "_")
            video_filename = f"got_video_{safe_title}_{hash(audio_path) % 10000}.mp4"
            output_path = self.config.temp_dir / video_filename

            success = await self._create_video_with_ffmpeg(
                image_paths,
                audio_path,
                str(output_path),
                image_duration,
                script_data.get('script', '')  # fallback if script is missing
            )

            if success and output_path.exists():
                logger.info(f"Video created successfully: {output_path.name}")
                return str(output_path)
            else:
                logger.error("Video creation failed")
                return None

        except Exception as e:
            logger.error(f"Error in create_vertical_video: {e}")
            return None

    async def _create_video_with_ffmpeg(self, image_paths: List[str],
                                        audio_path: str, output_path: str,
                                        image_duration: float,
                                        script_text: str) -> bool:
        try:
            filter_complex = self._build_filter_complex(
                image_paths, image_duration, script_text)

            cmd = ['ffmpeg', '-y', '-loglevel', 'warning']

            for image_path in image_paths:
                cmd.extend([
                    '-loop', '1', '-t',
                    str(image_duration + 1), '-i', image_path
                ])

            cmd.extend(['-i', audio_path])
            cmd.extend(['-filter_complex', filter_complex])

            cmd.extend([
                '-map',
                '[base]',  # use final video stream
                '-map',
                f'{len(image_paths)}:a',
                '-c:v',
                'libx264',
                '-c:a',
                'aac',
                '-b:v',
                '2M',
                '-b:a',
                '128k',
                '-r',
                str(self.fps),
                '-pix_fmt',
                'yuv420p',
                '-movflags',
                '+faststart',
                '-shortest',
                output_path
            ])

            logger.debug("Running FFmpeg command:\n" + " ".join(cmd))
            logger.info("Starting FFmpeg video rendering...")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("FFmpeg completed successfully")
                return True
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error in _create_video_with_ffmpeg: {e}")
            return False

    async def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                duration = float(stdout.decode().strip())
                logger.info(f"Audio duration: {duration:.2f} seconds")
                return duration
            else:
                logger.error(f"ffprobe failed: {stderr.decode()}")
                return None
        except Exception as e:
            logger.error(f"Error in _get_audio_duration: {e}")
            return None

    def _build_filter_complex(self, image_paths: List[str],
                              image_duration: float, script_text: str) -> str:
        filters = []
        for i in range(len(image_paths)):
            scale_factor = 2 if i % 3 == 0 else 1.2 if i % 3 == 1 else 1.5
            zoom = "min(zoom+0.0015,1.5)" if i % 3 == 0 else "1" if i % 3 == 1 else "min(zoom-0.001,1.0)"
            x_movement = "'iw/2-(iw/zoom/2)'" if i % 3 != 1 else "'if(gte(on,1),x+2,0)'"
            filters.append(
                f"[{i}:v]scale={self.output_width * scale_factor}:{self.output_height * scale_factor}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={self.output_width}:{self.output_height},"
                f"zoompan=z='{zoom}':d={int(self.fps * image_duration)}:"
                f"x={x_movement}:y='ih/2-(ih/zoom/2)':"
                f"s={self.output_width}x{self.output_height},setpts=PTS-STARTPTS[v{i}]"
            )

        current_stream = "v0"
        if len(image_paths) > 1:
            for i in range(1, len(image_paths)):
                transition = "fadeblack" if i % 2 else "wiperight"
                offset = i * image_duration - 0.8
                filters.append(
                    f"[{current_stream}][v{i}]xfade=transition={transition}:duration=0.8:offset={offset}[fade{i}]"
                )
                current_stream = f"fade{i}"
            filters.append(
                f"[{current_stream}]eq=contrast=1.1:brightness=0.05:saturation=1.2[base]"
            )
        else:
            filters.append(
                f"[v0]fade=t=in:st=0:d=0.5,fade=t=out:st={image_duration-0.5}:d=0.5[base]"
            )

        subtitles = self._create_subtitle_filter(
            self._extract_key_phrases(script_text),
            image_duration * len(image_paths))
        if subtitles:
            filters.append(f"[base]{subtitles}[base]")

        return ";".join(filters)

    def _extract_key_phrases(self, script_text: str) -> List[str]:
        sentences = re.split(r'[.!?]+', script_text)
        key_phrases = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                if any(kw in sentence.lower() for kw in [
                        "what if", "secret", "truth", "hidden", "never",
                        "revealed"
                ]) or len(sentence) < 50:
                    key_phrases.append(sentence.upper())
        return key_phrases[:4]

    def _create_subtitle_filter(self, phrases: List[str],
                                total_duration: float) -> str:
        if not phrases:
            return ""
        phrase_duration = total_duration / len(phrases)
        filters = []
        for i, phrase in enumerate(phrases):
            start = i * phrase_duration
            end = (i + 1) * phrase_duration
            text = phrase.replace("'", "\\'").replace(":", "\\:")
            filters.append(
                f"drawtext=text='{text}':x=(w-text_w)/2:y=h-150:"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=48:fontcolor=white:borderw=3:bordercolor=black:"
                f"box=1:boxcolor=black@0.7:boxborderw=10:"
                f"enable='between(t,{start},{end})'")
        return ",".join(filters)
