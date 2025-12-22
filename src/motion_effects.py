import os
import logging
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip, ColorClip
from typing import List, Dict
from src.config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_CODEC, AUDIO_CODEC, VIDEO_PRESET, VIDEO_THREADS

logger = logging.getLogger(__name__)

class MotionEffectsComposer:
    """
    Applies motion effects (Ken Burns zoom/pan) to images and composes final video.
    """
    def __init__(self, font: str = None):
        """
        Initialize MotionEffectsComposer.
        
        Args:
            font: Optional font name. If not provided, uses default:
                  - AppleGothic (macOS, Korean support) if available
                  - Arial (fallback)
        """
        if font:
            self.font = font
        else:
            # Simple font detection: Check for Korean font availability
            self.font = "AppleGothic" if os.path.exists("/System/Library/Fonts/Supplemental/AppleGothic.ttf") else "Arial"

    def compose_video(self, scenes: List[Dict], audio_path: str = None, output_path: str = None, video_title: str = None):
        """
        Composes final video from scene images with motion effects and subtitles.
        Supports both unified audio (legacy) and per-scene audio (new).
        
        Args:
            scenes: List of scene dicts with 'image_path', 'audio_text', 'duration', and optionally 'audio_path'
            audio_path: Optional unified audio file (legacy mode)
            output_path: Path to save the final video
            video_title: Optional title to display at the top of the video
        """
        logger.info("Composing video with motion effects...")
        print(f"\n   🎞️  [영상 합성 시작]")
        print(f"   총 장면 수: {len(scenes)}")
        
        # Check if using per-scene audio or unified audio
        per_scene_audio = any(scene.get('audio_path') for scene in scenes)
        
        if per_scene_audio:
            print(f"   오디오 모드: 장면별 개별 오디오 (정확한 타이밍)\n")
        else:
            print(f"   오디오 모드: 통합 오디오 (레거시)\n")
            if audio_path and os.path.exists(audio_path):
                full_audio = AudioFileClip(audio_path)
                print(f"   🔊 전체 오디오 길이: {full_audio.duration:.2f}초\n")
            else:
                print(f"   ⚠️  오디오 파일 없음, 무음 영상으로 생성\n")
                full_audio = None
        
        clips = []
        
        try:
            # Process each scene
            for idx, scene in enumerate(scenes, 1):
                asset_path = scene.get('video_path') or scene.get('image_path')
                duration = scene.get('duration', 3)
                text = scene.get('audio_text', '')
                scene_audio_path = scene.get('audio_path')
                
                print(f"   📹 Scene {idx}/{len(scenes)}: {text[:30]}... ({duration:.2f}초)")
                
                # Check if file exists
                if asset_path and asset_path.endswith('.mp4') and not os.path.exists(asset_path):
                    png_path = asset_path.replace('.mp4', '.png')
                    if os.path.exists(png_path):
                        asset_path = png_path
                
                if not asset_path or not os.path.exists(asset_path):
                    logger.warning(f"Asset file missing: {asset_path}")
                    print(f"      ⚠️  파일 없음: {asset_path}")
                    continue
                
                clip = None
                
                # Image files: Apply Ken Burns effect
                if asset_path.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    clip = self._apply_ken_burns_effect(asset_path, duration)
                else:
                    # Video files: Simple resize/crop
                    clip = VideoFileClip(asset_path)
                    clip = self._resize_clip(clip, duration)

                # Add per-scene audio if available
                if per_scene_audio and scene_audio_path and os.path.exists(scene_audio_path):
                    scene_audio = AudioFileClip(scene_audio_path)
                    original_audio_duration = scene_audio.duration
                    
                    # CRITICAL: Match audio duration to clip duration WITHOUT looping
                    if scene_audio.duration > duration:
                        # If audio is longer, trim it to exact duration
                        scene_audio = scene_audio.subclipped(0, duration)
                    elif scene_audio.duration < duration:
                        # If audio is shorter, pad with silence (NEVER loop)
                        from moviepy.audio.AudioClip import AudioArrayClip
                        import numpy as np
                        
                        # Use consistent fps
                        audio_fps = getattr(scene_audio, 'fps', 44100)
                        if audio_fps is None:
                            audio_fps = 44100
                        
                        audio_array = scene_audio.to_soundarray(fps=audio_fps)
                        silence_duration = duration - scene_audio.duration
                        silence_samples = int(silence_duration * audio_fps)
                        
                        # Create silence with same channel structure
                        if len(audio_array.shape) == 1:
                            silence = np.zeros(silence_samples)
                            extended_audio = np.concatenate([audio_array, silence])
                        else:
                            silence = np.zeros((silence_samples, audio_array.shape[1]))
                            extended_audio = np.vstack([audio_array, silence])
                        
                        scene_audio = AudioArrayClip(extended_audio, fps=audio_fps)
                    
                    # Use subclipped to set exact duration (avoids looping)
                    try:
                        if hasattr(scene_audio, 'subclipped'):
                            scene_audio = scene_audio.subclipped(0, min(scene_audio.duration, duration))
                        elif hasattr(scene_audio, 'subclip'):
                            scene_audio = scene_audio.subclip(0, min(scene_audio.duration, duration))
                    except:
                        pass  # Already correct duration
                    
                    clip = self._add_audio_to_clip(clip, scene_audio)
                    print(f"      🔊 장면 오디오 추가 (원본: {original_audio_duration:.2f}초 → 클립: {duration:.2f}초, 반복 없음)")

                # Add subtitles (center position, split for faster transitions)
                if text and clip:
                    clip = self._add_subtitle(clip, text, duration)
                
                if clip:
                    # Ensure exact duration
                    clip = self._set_exact_duration(clip, duration)
                    clips.append(clip)
                    print(f"      ✅ 완료 (실제 길이: {clip.duration:.2f}초)")

            if not clips:
                logger.error("No valid clips to compose.")
                print(f"\n   ❌ 합성할 클립이 없습니다.\n")
                return None

            print(f"\n   🔗 클립 연결 중...")
            # Concatenate all clips
            # Use method="compose" to preserve audio from each clip
            # If per_scene_audio, each clip already has its audio, so don't add overall audio
            final_video = concatenate_videoclips(clips, method="compose")
            print(f"   ✅ 최종 비디오 길이: {final_video.duration:.2f}초\n")
            
            # Ensure no duplicate audio: if per_scene_audio, each clip already has audio
            # Don't add overall audio again
            
            # Add title overlay to entire video if provided
            if video_title:
                # Extract first sentence only
                first_sentence = self._extract_first_sentence(video_title)
                print(f"   📌 제목 추가 중: {first_sentence[:30]}...")
                
                # YouTube Shorts top margin: avoid overlapping with channel icon/follow button
                TOP_MARGIN = 80  # pixels from top to avoid YouTube UI elements
                
                # Adaptive Font Sizing Strategy
                # 1. Short title (<15 chars) -> 100px (Impact)
                # 2. Medium title (15-25 chars) -> 80px (Safe)
                # 3. Long title (>25 chars) -> 65px (Prevent Overflow)
                
                # Use total length INCLUDING SPACES for accurate sizing
                title_len = len(first_sentence)
                if title_len < 15:
                    font_size = 100
                    line_height_factor = 1.2
                elif title_len < 25:
                    font_size = 80
                    line_height_factor = 1.25
                else:
                    font_size = 65
                    line_height_factor = 1.3
                
                # Use MoviePy's automatic word wrapping (simpler, respects word boundaries)
                title_text = first_sentence
                
                # Create text clip with automatic word wrapping
                title_clip = TextClip(
                    text=title_text,
                    font_size=font_size,  # Adaptive font size
                    color='white',
                    font=self.font,
                    stroke_color='black',
                    stroke_width=4,  # Thicker stroke for larger font
                    size=(864, None),  # 80% of 1080px width, auto word-wrap
                    method='caption',  # Auto-wrap + center alignment
                    text_align='center',  # Explicit center alignment
                    duration=final_video.duration
                )
                
                # Estimate number of lines for background height calculation
                avg_chars_per_line = 12  # Approximate for Korean with this font size
                num_lines = max(1, (len(title_text) + avg_chars_per_line - 1) // avg_chars_per_line)
                line_height = int(font_size * line_height_factor)
                text_height = num_lines * line_height
                
                # Background height should cover the TOP_MARGIN plus the text area and padding
                # New height = TOP_MARGIN + text_height + bottom padding (40px)
                bg_height = int(TOP_MARGIN + text_height + 40)
                # Ensure minimum height
                bg_height = max(bg_height, 150)
                
                bg_width = VIDEO_WIDTH  # Full width (9:16 video width)
                
                print(f"      📐 제목 배경: {num_lines}줄, 높이 {bg_height}px (상단 0px부터 시작)")
                
                bg_clip = ColorClip(
                    size=(bg_width, bg_height),
                    color=(0, 0, 0),  # Black
                    duration=final_video.duration
                )
                
                # Position background at absolute top (0 pixels from top)
                try:
                    bg_clip = bg_clip.with_position(('center', 0))
                except AttributeError:
                    bg_clip = bg_clip.set_position(('center', 0))
                
                # Position text: TOP_MARGIN + padding
                # We want text to start after the TOP_MARGIN
                text_y_position = TOP_MARGIN + 50  # 50px padding below UI area (더 아래로)
                
                try:
                    title_clip = title_clip.with_position(('center', text_y_position))
                except AttributeError:
                    title_clip = title_clip.set_position(('center', text_y_position))
                
                # Composite: video + background + text
                final_video = CompositeVideoClip([final_video, bg_clip, title_clip])
                print(f"   ✅ 제목 추가 완료 (검정 배경 포함)\n")
            
            # Add unified audio if not using per-scene audio
            if not per_scene_audio and full_audio:
                print(f"   🔊 통합 오디오 추가 중...")
                video_duration = final_video.duration
                audio_duration = full_audio.duration
                
                if abs(video_duration - audio_duration) > 0.1:
                    print(f"   ⚠️  길이 차이: {abs(video_duration - audio_duration):.2f}초")
                    full_audio = self._set_exact_duration(full_audio, video_duration, is_audio=True)
                
                final_video = self._add_audio_to_clip(final_video, full_audio)

            logger.info(f"Writing video to {output_path}")
            print(f"\n   🎬 [영상 렌더링 중] 이 작업은 시간이 걸릴 수 있습니다...\n")
            final_video.write_videofile(
                output_path, 
                fps=VIDEO_FPS, 
                codec=VIDEO_CODEC, 
                audio_codec=AUDIO_CODEC,
                preset=VIDEO_PRESET,
                threads=VIDEO_THREADS
            )
            
            # Clean up
            final_video.close()
            if not per_scene_audio and full_audio:
                full_audio.close()
            for clip in clips:
                clip.close()
            
            print(f"\n   ✅ 영상 저장 완료: {output_path}\n")
            return output_path

        except Exception as e:
            logger.error(f"Error composing video: {e}")
            import traceback
            print(f"\n{'='*50}")
            print(f"  ❌ [에러 발생] 영상 합성 실패")
            print(f"{'='*50}")
            print(f"   에러 내용: {str(e)}")
            print(f"   에러 타입: {type(e).__name__}")
            print(f"   {'─'*46}")
            print(f"   상세 에러:")
            print(f"   {traceback.format_exc()}")
            print(f"   {'─'*46}")
            print(f"   💡 해결 방법:")
            print(f"      - MoviePy 버전 확인: pip install --upgrade moviepy")
            print(f"      - 이미지와 오디오 파일이 output/ 폴더에 있는지 확인")
            print(f"      - FFmpeg 설치 확인: brew install ffmpeg (macOS)")
            print(f"{'='*50}\n")
            return None

    def _apply_ken_burns_effect(self, image_path: str, duration: float):
        """
        Applies Ken Burns (slow zoom) effect to a static image.
        Creates a gentle zoom from 1.0x to 1.05x over the duration.
        """
        # Load image clip
        img_clip = ImageClip(image_path)
        
        # Target size for vertical video (9:16 ratio)
        target_width, target_height = VIDEO_WIDTH, VIDEO_HEIGHT
        
        # First, ensure the image is at least 1080x1920
        # Scale UP if needed (important for Ken Burns effect to work properly)
        if img_clip.h < target_height or img_clip.w < target_width:
            scale_h = target_height / img_clip.h if img_clip.h < target_height else 1
            scale_w = target_width / img_clip.w if img_clip.w < target_width else 1
            scale = max(scale_h, scale_w) * 1.15  # Scale up 15% extra for zoom room
            
            new_height = int(img_clip.h * scale)
            img_clip = img_clip.resized(height=new_height)
        
        # If image is already large, just ensure we have room for zoom
        elif img_clip.w / img_clip.h < (target_width / target_height):
            # Image is taller/narrower - fit to width with extra room
            scale = (target_width * 1.15) / img_clip.w
            new_height = int(img_clip.h * scale)
            img_clip = img_clip.resized(height=new_height)
        else:
            # Image is wider - fit to height with extra room
            scale = (target_height * 1.15) / img_clip.h
            new_height = int(img_clip.h * scale)
            img_clip = img_clip.resized(height=new_height)
        
        # Now crop to center at 1080x1920 (this is our starting frame)
        if img_clip.w > target_width or img_clip.h > target_height:
            x_center = img_clip.w / 2
            y_center = img_clip.h / 2
            img_clip = img_clip.cropped(
                x_center=x_center, 
                y_center=y_center,
                width=target_width, 
                height=target_height
            )
        
        # Apply subtle zoom effect (1.0 → 1.05 instead of 1.1)
        # Smaller zoom = more image visible
        def zoom_func(t):
            progress = min(t / duration, 1.0)  # Clamp to 0-1
            return 1.0 + 0.05 * progress  # Zoom from 1.0x to 1.05x
        
        # Apply zoom - this will make the clip slightly larger
        zoomed = img_clip.resized(zoom_func)
        
        # Crop back to 1080x1920, taking the center of the zoomed image
        # This maintains the Ken Burns effect while keeping the target size
        final_clip = zoomed.cropped(
            x_center=target_width/2, 
            y_center=target_height/2,
            width=target_width, 
            height=target_height
        )
        
        # Set exact duration
        final_clip = self._set_exact_duration(final_clip, duration)
        
        return final_clip
    
    def _resize_clip(self, clip, duration: float):
        """Resize video clip to 9:16 format."""
        clip = clip.resized(height=VIDEO_HEIGHT)
        clip = clip.cropped(x_center=clip.w/2, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
        clip = self._set_exact_duration(clip, duration)
        return clip
    
    def _set_exact_duration(self, clip, duration: float, is_audio: bool = False):
        """
        Set exact duration for a clip (compatible with both MoviePy v1 and v2).
        
        Args:
            clip: Video or audio clip
            duration: Target duration
            is_audio: If True, don't loop audio - pad with silence instead
        """
        try:
            # Try MoviePy v2 method first
            return clip.with_duration(duration)
        except AttributeError:
            # Fallback to MoviePy v1 method
            try:
                return clip.set_duration(duration)
            except AttributeError:
                # If both fail, use subclip
                if clip.duration > duration:
                    return clip.subclip(0, duration)
                else:
                    # For audio, don't loop - pad with silence instead
                    if is_audio:
                        from moviepy.audio.AudioClip import AudioArrayClip
                        import numpy as np
                        # Get audio array
                        audio_array = clip.to_soundarray(fps=clip.fps)
                        # Calculate silence needed
                        silence_duration = duration - clip.duration
                        silence_samples = int(silence_duration * clip.fps)
                        # Create silence array
                        if len(audio_array.shape) == 1:
                            silence = np.zeros(silence_samples)
                            extended_audio = np.concatenate([audio_array, silence])
                        else:
                            silence = np.zeros((silence_samples, audio_array.shape[1]))
                            extended_audio = np.vstack([audio_array, silence])
                        return AudioArrayClip(extended_audio, fps=clip.fps)
                    else:
                        # For video, loop if shorter
                        loops = int(duration / clip.duration) + 1
                        from moviepy import concatenate_videoclips
                        return concatenate_videoclips([clip] * loops).subclip(0, duration)
    
    def _add_audio_to_clip(self, video_clip, audio_clip):
        """Add audio to video clip (compatible with both MoviePy v1 and v2)."""
        try:
            # Try MoviePy v2 method first
            return video_clip.with_audio(audio_clip)
        except AttributeError:
            # Fallback to MoviePy v1 method
            try:
                return video_clip.set_audio(audio_clip)
            except AttributeError as e:
                print(f"   ⚠️  오디오 추가 실패: {e}")
                return video_clip

    def _extract_first_sentence(self, text: str) -> str:
        """
        Extract the first sentence from the title.
        Splits by Korean/English sentence endings: . ! ? 。 ！ ？
        Also handles common Korean sentence ending patterns.
        
        Args:
            text: Full title text
        
        Returns:
            First sentence only
        """
        import re
        
        # First, try to find explicit sentence endings
        # Pattern: text followed by sentence-ending punctuation
        match = re.search(r'^(.+?[.!?。！？])', text)
        if match:
            return match.group(1).strip()
        
        # If no sentence ending, look for common Korean separators
        # e.g., "제목 - 설명" or "제목: 설명" or "제목, 설명"
        separators = [' - ', ': ', '｜', '|', ' / ']
        for sep in separators:
            if sep in text:
                first_part = text.split(sep)[0].strip()
                if len(first_part) > 5:  # Ensure it's meaningful
                    return first_part
        
        # Look for a comma followed by a space as a potential break point
        if ', ' in text:
            first_part = text.split(', ')[0].strip()
            if len(first_part) > 10:  # Only if it's substantial
                return first_part
        
        # If text is short enough, return as is
        if len(text) <= 40:
            return text.strip()
        
        # Last resort: truncate at 40 characters, try to break at word boundary
        truncated = text[:40]
        last_space = truncated.rfind(' ')
        if last_space > 20:
            return truncated[:last_space].strip()
        
        return truncated.strip()
    
    def _split_title_into_balanced_lines(self, text: str, max_width: int = 1000, font_size: int = 75) -> List[str]:
        """
        Split title text into balanced lines using word boundaries.
        Optimized for visual balance (avoiding orphans/long-short splits).
        """
        words = text.split()
        if not words:
            return [text]
            
        total_len = len(text)  # Includes spaces
        if total_len < 10:  # Very short, keep one line
            return [text]
            
        # Target balanced split (approximately half)
        target_len = total_len / 2
        
        best_split_idx = -1
        min_diff = float('inf')
        
        current_len = 0
        for i, word in enumerate(words):
            # Check length if we split AFTER this word
            # Length of first part would be current_len + word_len
            word_len = len(word)
            len_if_split = current_len + word_len
            
            diff = abs(len_if_split - target_len)
            
            if diff < min_diff:
                min_diff = diff
                best_split_idx = i
                
            # Add word len + space for next iteration
            current_len += word_len + 1
            
        # Split at the best index
        if best_split_idx >= 0 and best_split_idx < len(words) - 1:
            line1 = " ".join(words[:best_split_idx+1])
            line2 = " ".join(words[best_split_idx+1:])
            
            # Special check: If line2 is just 1 very short word (orphan), just keep as 1 line
            if len(words) > 2 and len(line2) < 4:
                return [text]
                
            return [line1, line2]
            
        return [text]
    
    def _split_text_for_subtitle(self, text: str, max_length: int = 25) -> List[tuple]:
        """
        Split text into shorter segments for subtitle display.
        IMPORTANT: Never split in the middle of a word!
        Duration is proportional to character count for better sync with narration.
        
        Args:
            text: Full text to split
            max_length: Maximum characters per subtitle segment (default 25 for Korean)
        
        Returns:
            List of (text_segment, duration_ratio) tuples with proportional timing
        """
        text = text.strip()
        if not text:
            return [(text, 1.0)]
        
        if len(text) <= max_length:
            return [(text, 1.0)]
        
        segments = []
        
        # First, try to split by natural sentence breaks (,. ! ? etc.)
        import re
        # Split by sentence-ending punctuation while keeping the punctuation
        sentence_parts = re.split(r'([.!?。！？,，]+\s*)', text)
        
        current_segment = ""
        for part in sentence_parts:
            if not part:
                continue
            
            test_segment = current_segment + part
            
            if len(test_segment) <= max_length:
                current_segment = test_segment
            else:
                # Current segment is full, save it
                if current_segment.strip():
                    segments.append(current_segment.strip())
                
                # Check if this part itself is too long
                if len(part) <= max_length:
                    current_segment = part
                else:
                    # Split long part by SPACES to avoid breaking words
                    words = part.split()
                    current_segment = ""
                    for word in words:
                        test_word = (current_segment + " " + word).strip() if current_segment else word
                        if len(test_word) <= max_length:
                            current_segment = test_word
                        else:
                            if current_segment.strip():
                                segments.append(current_segment.strip())
                            current_segment = word
                    # Don't append here, let the loop continue
        
        # Add remaining text
        if current_segment.strip():
            segments.append(current_segment.strip())
        
        # If no segments, return original text
        if not segments:
            return [(text, 1.0)]
        
        # Calculate duration ratios PROPORTIONAL to character count
        total_chars = sum(len(seg) for seg in segments)
        if total_chars == 0:
            ratio = 1.0 / len(segments)
            return [(seg, ratio) for seg in segments]
        
        result = []
        for seg in segments:
            char_ratio = len(seg) / total_chars
            result.append((seg, char_ratio))
        
        return result
    
    def _add_subtitle(self, clip, text: str, duration: float):
        """Adds a subtitle overlay to a clip at the center of the screen."""
        try:
            # Split text into shorter segments for faster transitions
            text_segments = self._split_text_for_subtitle(text, max_length=25)
            
            subtitle_clips = []
            current_time = 0
            
            # Define impact keywords for highlighting (REDUCED list for key moments only)
            # Only first-word matches trigger emphasis to avoid over-highlighting
            impact_keywords_strict = [
                "절대", "경고", "비밀", "정답", "비법"
            ]
            
            for segment_text, duration_ratio in text_segments:
                segment_duration = duration * duration_ratio
                
                # STRICT CHECK: Only highlight if segment STARTS with a key impact word
                words = segment_text.split()
                first_word = words[0] if words else ""
                is_impactful = any(first_word.startswith(k) for k in impact_keywords_strict)
                
                # Dynamic styling (simplified - only first-word matches trigger color)
                text_color = '#FFD700' if is_impactful else 'white'  # Gold for impact, white for normal
                stroke_width = 4 if is_impactful else 3
                font_size = 85 if is_impactful else 80  # Slightly larger for emphasis
                
                txt_clip = TextClip(
                    text=segment_text, 
                    font_size=font_size,
                    color=text_color, 
                    font=self.font,
                    stroke_color='black', 
                    stroke_width=stroke_width,
                    size=(960, None),  # 좌우 60px 여백 확보 (1080 - 120)
                    method='caption',
                    text_align='center',
                    duration=segment_duration
                )

                
                # Set position to center of screen (compatible with both versions)
                try:
                    txt_clip = txt_clip.with_position(('center', 0.5), relative=True)
                except AttributeError:
                    # Fallback for older MoviePy versions
                    txt_clip = txt_clip.set_position(('center', 0.5), relative=True)
                
                # Set timing
                try:
                    txt_clip = txt_clip.with_start(current_time)
                except AttributeError:
                    txt_clip = txt_clip.set_start(current_time)
                
                subtitle_clips.append(txt_clip)
                current_time += segment_duration
            
            # Combine all subtitle clips
            if subtitle_clips:
                return CompositeVideoClip([clip] + subtitle_clips)
            else:
                return clip
                
        except Exception as e:
            logger.warning(f"Failed to add subtitle: {e}")
            # Return clip without subtitle if subtitle fails
            return clip
    
    def _add_title(self, clip, title: str, duration: float):
        """Adds a title overlay at the top of the video."""
        try:
            title_clip = TextClip(
                text=title,
                font_size=60,
                color='white',
                font=self.font,
                stroke_color='black',
                stroke_width=2,
                size=(1000, None),
                method='caption',  # 'caption' method automatically centers text
                duration=duration
            )
            
            # Position at top center (10% from top)
            try:
                title_clip = title_clip.with_position(('center', 0.1), relative=True)
            except AttributeError:
                title_clip = title_clip.set_position(('center', 0.1), relative=True)
            
            return CompositeVideoClip([clip, title_clip])
        except Exception as e:
            logger.warning(f"Failed to add title: {e}")
            return clip

if __name__ == "__main__":
    composer = MotionEffectsComposer()
    # composer.compose_video(...)
