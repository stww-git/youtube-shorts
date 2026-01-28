import os
import logging
import tempfile
from pathlib import Path
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip, ColorClip
from moviepy.audio.AudioClip import concatenate_audioclips, CompositeAudioClip
from typing import List, Dict
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 로컬 config import
from config.model_config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_CODEC, AUDIO_CODEC, VIDEO_PRESET, VIDEO_THREADS
from title_image_generator import create_title_image

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

    def compose_video(self, scenes: List[Dict], audio_path: str = None, output_path: str = None, video_title: str = None, summary_checklist: list = None, summary_card_duration: float = 3.0, include_disclaimer: bool = True, bgm_enabled: bool = False, bgm_volume: float = 0.1, bgm_file: str = None):
        """
        Composes final video from scene images with motion effects and subtitles.
        Supports both unified audio (legacy) and per-scene audio (new).
        
        Args:
            scenes: List of scene dicts with 'image_path', 'audio_text', 'duration', and optionally 'audio_path'
            audio_path: Optional unified audio file (legacy mode)
            output_path: Path to save the final video
            video_title: Optional title to display at the top of the video
            summary_checklist: Optional list of checklist items for final summary card
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
                
                # === Medical Disclaimer (Last Scene Only, if enabled) ===
                if idx == len(scenes) and include_disclaimer:
                    print(f"      🏥 의료 면책 조항 추가 (하단, {duration}초)")
                    clip = self._add_medical_disclaimer(clip, duration)
                
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
            print(f"   ✅ 최종 비디오 길이: {final_video.duration:.2f}초")
            
            # === Summary Card (핵심 정보 카드) ===
            if summary_checklist:
                summary_card = self._create_summary_card(summary_checklist, duration=summary_card_duration)
                if summary_card:
                    final_video = concatenate_videoclips([final_video, summary_card], method="compose")
                    print(f"   ✅ 핵심 정보 카드 추가됨 (+0.5초)")
            
            print(f"   ✅ 최종 비디오 길이 (카드 포함): {final_video.duration:.2f}초\n")
            
            # Ensure no duplicate audio: if per_scene_audio, each clip already has audio
            # Don't add overall audio again
            
            # Add title overlay to entire video if provided
            if video_title:
                # Extract first sentence only
                first_sentence = self._extract_first_sentence(video_title)
                print(f"   📌 제목 추가 중: {first_sentence[:30]}...")
                
                # YouTube Shorts top margin: avoid overlapping with channel icon/follow button
                TOP_MARGIN = 100
                
                from config.title_config import TITLE_FONT_PATH, TITLE_LINE_COLORS, get_adaptive_title_style
                title_font = TITLE_FONT_PATH
                title_text = first_sentence
                
                # Adaptive Font Sizing
                font_size, line_height_factor = get_adaptive_title_style(len(title_text))
                
                # === NEW: Pillow-based title generation (tight letter spacing) ===
                use_pillow_title = True  # Set to False to use old TextClip method
                
                if use_pillow_title:
                    try:
                        # Create title image with customized line colors (from config)
                        title_image_path = create_title_image(
                            text=title_text,
                            font_size=font_size,
                            font_path=title_font,
                            line_colors=TITLE_LINE_COLORS
                        )
                        
                        # Load as ImageClip
                        title_clip = ImageClip(title_image_path)
                        # Fix: Use _set_exact_duration for compatibility
                        title_clip = self._set_exact_duration(title_clip, final_video.duration)
                        
                        # Get actual image dimensions for background
                        from PIL import Image as PILImage
                        with PILImage.open(title_image_path) as img:
                            title_img_height = img.height
                        
                        print(f"      🎨 Pillow 방식 사용 (자간: -5px)")
                        
                    except Exception as e:
                        logger.warning(f"Pillow title failed: {e}. Falling back to TextClip.")
                        use_pillow_title = False
                
                if not use_pillow_title:
                    # OLD METHOD: TextClip (wide letter spacing)
                    title_clip = TextClip(
                        text=title_text,
                        font_size=font_size,
                        color='white',
                        font=title_font,
                        stroke_color='black',
                        stroke_width=5,
                        size=(900, None),
                        method='caption',
                        text_align='center',
                        duration=final_video.duration
                    )
                    title_img_height = None  # Will use estimate
                    print(f"      📝 TextClip 방식 사용 (기본 자간)")
                
                # Calculate background height
                if use_pillow_title and title_img_height:
                    bg_height = int(TOP_MARGIN + title_img_height + 40)
                else:
                    avg_chars_per_line = 10
                    num_lines = max(1, (len(title_text) + avg_chars_per_line - 1) // avg_chars_per_line)
                    line_height = int(font_size * line_height_factor)
                    text_height = num_lines * line_height
                    bg_height = int(TOP_MARGIN + text_height + 40)
                
                bg_height = max(bg_height, 180)
                bg_width = VIDEO_WIDTH
                
                print(f"      📐 제목 배경: 높이 {bg_height}px, 폰트 {font_size}px")
                
                bg_clip = ColorClip(
                    size=(bg_width, bg_height),
                    color=(0, 0, 0),
                    duration=final_video.duration
                )
                
                try:
                    bg_clip = bg_clip.with_position(('center', 0))
                except AttributeError:
                    bg_clip = bg_clip.set_position(('center', 0))
                
                # Position title
                text_y_position = TOP_MARGIN + 20
                
                try:
                    title_clip = title_clip.with_position(('center', text_y_position))
                except AttributeError:
                    title_clip = title_clip.set_position(('center', text_y_position))
                
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

            # === BGM Overlay ===
            if bgm_enabled and bgm_file:
                print(f"\n   🎵 [배경음악 추가]")
                bgm_path = Path(__file__).parent.parent.parent.parent / "assets" / "bgm" / bgm_file
                if bgm_path.exists():
                    try:
                        bgm_audio = AudioFileClip(str(bgm_path))
                        video_duration = final_video.duration
                        
                        # Loop BGM if shorter than video
                        if bgm_audio.duration < video_duration:
                            loop_count = int(video_duration / bgm_audio.duration) + 1
                            bgm_audio = concatenate_audioclips([bgm_audio] * loop_count)
                            print(f"      🔁 BGM 루프: {loop_count}회 반복")
                        
                        # Trim to video length
                        bgm_audio = bgm_audio.subclipped(0, video_duration)
                        
                        # Adjust volume
                        bgm_audio = bgm_audio.with_volume_scaled(bgm_volume)
                        print(f"      🔊 볼륨: {bgm_volume * 100:.0f}%")
                        
                        # Mix with existing audio
                        if final_video.audio:
                            mixed_audio = CompositeAudioClip([final_video.audio, bgm_audio])
                            final_video = final_video.with_audio(mixed_audio)
                        else:
                            final_video = final_video.with_audio(bgm_audio)
                        
                        print(f"      ✅ 배경음악 추가 완료: {bgm_file}")
                    except Exception as e:
                        print(f"      ⚠️ BGM 추가 실패: {e}")
                else:
                    print(f"      ⚠️ BGM 파일을 찾을 수 없습니다: {bgm_path}")

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
        
        
        # Comma splitting removed - show full title instead
        
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
    
    def _split_by_char_ratio(self, words: list, targets: list) -> list:
        """
        글자수 비율로 어절 목록을 분할합니다.
        어절 경계를 유지하면서 목표 글자수에 가장 가까운 지점에서 분할합니다.
        
        Args:
            words: 어절 목록
            targets: 분할 목표 글자수 리스트 (누적값, 예: [7, 14, 21])
        
        Returns:
            분할된 문자열 리스트
        """
        if not words:
            return []
        
        # 각 어절까지의 누적 글자수 계산 (공백 제외)
        cumulative_chars = []
        total = 0
        for w in words:
            total += len(w)
            cumulative_chars.append(total)
        
        parts = []
        prev_idx = 0
        
        for target in targets[:-1]:  # 마지막 target은 전체 길이이므로 제외
            # 목표 글자수에 가장 가까운 어절 경계 찾기
            best_idx = prev_idx
            min_diff = float('inf')
            
            for i in range(prev_idx, len(words)):
                diff = abs(cumulative_chars[i] - target)
                if diff < min_diff:
                    min_diff = diff
                    best_idx = i
            
            # 분할점이 이전과 같으면 최소 1어절 포함
            if best_idx == prev_idx and prev_idx < len(words) - 1:
                best_idx = prev_idx
            
            # 파트 추가
            part = " ".join(words[prev_idx:best_idx + 1])
            if part:
                parts.append(part)
            prev_idx = best_idx + 1
        
        # 남은 어절 추가
        if prev_idx < len(words):
            remaining = " ".join(words[prev_idx:])
            if remaining:
                parts.append(remaining)
        
        return parts
    
    def _create_subtitle_image(self, text, style):
        """Creates a subtitle image using Pillow to avoid MoviePy trimming issues."""
        try:

            
            # Unpack style
            font_path = style.get('font_path', self.font)
            font_size = style.get('font_size', 80)
            from config.subtitle_config import (
                get_keyword_color, 
                SUBTITLE_TEXT_COLOR, 
                SUBTITLE_STROKE_COLOR, 
                SUBTITLE_STROKE_WIDTH, 
                SUBTITLE_MAX_WIDTH
            )
            
            # Unpack style with config defaults
            font_path = style.get('font_path', self.font)
            font_size = style.get('font_size', 80)
            text_color = style.get('text_color', SUBTITLE_TEXT_COLOR)
            stroke_color = style.get('stroke_color', SUBTITLE_STROKE_COLOR)
            stroke_width = style.get('stroke_width', SUBTITLE_STROKE_WIDTH)
            max_width = style.get('max_width', SUBTITLE_MAX_WIDTH)
            
            # Load font
            try:
                font = ImageFont.truetype(font_path, font_size)
            except:
                font = ImageFont.load_default()
            
            # Wrap text and calculate layout
            dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            words = text.split()
            line_layouts = [] # Each element is a list of {'text': word, 'width': w, 'color': color}
            current_line_words = []
            current_line_width = 0
            
            # Calculate space width once
            space_width = dummy_draw.textbbox((0, 0), " ", font=font)[2] - dummy_draw.textbbox((0, 0), " ", font=font)[0]
            
            for word in words:
                word_bbox = dummy_draw.textbbox((0, 0), word, font=font)
                word_width = word_bbox[2] - word_bbox[0]
                
                # Check if adding this word exceeds max_width
                # If current_line_words is empty, it's the first word, so add it regardless
                # Otherwise, check if current_line_width + space + word_width > max_width
                if current_line_words and (current_line_width + space_width + word_width > max_width):
                    # Start a new line
                    line_layouts.append(current_line_words)
                    current_line_words = []
                    current_line_width = 0
                
                # Add word to current line
                color = get_keyword_color(word, text_color)
                current_line_words.append({
                    "text": word,
                    "width": word_width,
                    "color": color
                })
                current_line_width += word_width
                if len(current_line_words) > 1: # Add space width only if it's not the first word on the line
                    current_line_width += space_width
            
            # Add any remaining words as the last line
            if current_line_words:
                line_layouts.append(current_line_words)
            
            # Calculate total image size based on line_layouts
            line_spacing = 10
            total_text_height = 0
            max_line_width = 0
            line_heights = [] # Store height for each line
            
            for line_data in line_layouts:
                line_max_word_height = 0
                line_total_width = 0
                for i, word_info in enumerate(line_data):
                    # Recalculate bbox for height, as it might vary slightly
                    bbox = dummy_draw.textbbox((0, 0), word_info['text'], font=font)
                    h = bbox[3] - bbox[1]
                    line_max_word_height = max(line_max_word_height, h)
                    
                    line_total_width += word_info['width']
                    if i < len(line_data) - 1:
                        line_total_width += space_width
                
                line_heights.append(line_max_word_height)
                total_text_height += line_max_word_height
                max_line_width = max(max_line_width, line_total_width)
            
            total_text_height += line_spacing * (len(line_layouts) - 1)
            
            # Add padding for stroke
            padding = stroke_width * 2 + 10
            img_width = max_line_width + padding * 2
            img_height = total_text_height + padding * 2
            
            # Create image
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw text
            current_y = padding
            for line_idx, line_data in enumerate(line_layouts):
                # Calculate total line width for centering
                line_total_width = 0
                for i, word_info in enumerate(line_data):
                    line_total_width += word_info['width']
                    if i < len(line_data) - 1:
                        line_total_width += space_width
                        
                # Center alignment
                start_x = (img_width - line_total_width) // 2
                current_x = start_x
                
                for i, word_info in enumerate(line_data):
                    word_text = word_info['text']
                    color = word_info['color']
                    
                    # Draw stroke
                    if stroke_width > 0:
                        for dx in range(-stroke_width, stroke_width + 1):
                            for dy in range(-stroke_width, stroke_width + 1):
                                if dx == 0 and dy == 0: continue
                                # Optimized circular stroke
                                if dx*dx + dy*dy > stroke_width*stroke_width + 1: continue 
                                draw.text((current_x + dx, current_y + dy), word_text, font=font, fill=stroke_color)
                    
                    # Draw main text
                    draw.text((current_x, current_y), word_text, font=font, fill=color)
                    
                    current_x += word_info['width']
                    if i < len(line_data) - 1:
                        current_x += space_width
                
                # Move to next line
                current_y += line_heights[line_idx] + line_spacing
            
            # Save to temp file to verify transparency support in all MoviePy versions
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
                img.save(tf.name)
                return tf.name
            
        except Exception as e:
            logger.error(f"Failed to create subtitle image: {e}")
            return None

    def _add_medical_disclaimer(self, clip, duration):
        """
        Adds a medical disclaimer overlay to the bottom of the clip using Pillow.
        Text: Multi-line health message
        Args:
            clip: Video clip to overlay on
            duration: Duration in seconds for the disclaimer to appear
        """
        try:
            text = "주기적인 건강검진이 필요해요\n여러분의 건강을 진심으로 응원합니다"
            font_size = 42
            text_color = "white"
            stroke_color = "black"
            stroke_width = 3
            line_spacing = 10  # 줄 간격
            
            # Load font - 면책 조항 전용 폰트 (NanumSquareB)
            from pathlib import Path
            disclaimer_font_path = Path(__file__).parent.parent / "fonts" / "nanumsquare" / "NanumSquareB.ttf"
            try:
                font = ImageFont.truetype(str(disclaimer_font_path), font_size)
            except:
                # Fallback to self.font
                try:
                    font = ImageFont.truetype(self.font, font_size)
                except:
                    font = ImageFont.load_default()
            
            # Calculate text size (Multi-line)
            dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            # textbbox supports multiline by default in newer Pillow versions
            bbox = dummy_draw.textbbox((0, 0), text, font=font, spacing=line_spacing, align='center')
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Create image with padding
            padding = 20
            img_width = int(text_width + padding * 2 + stroke_width * 2)
            img_height = int(text_height + padding * 2 + stroke_width * 2)
            
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw text with stroke (Multi-line)
            # Center the text
            x = (img_width - text_width) / 2
            y = padding + stroke_width
            
            # Stroke
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx*dx + dy*dy > stroke_width*stroke_width + 1: continue
                    draw.multiline_text((x+dx, y+dy), text, font=font, fill=stroke_color, spacing=line_spacing, align='center')
            
            # Main text
            draw.multiline_text((x, y), text, font=font, fill=text_color, spacing=line_spacing, align='center')
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
                img.save(tf.name)
                temp_path = tf.name
            
            print(f"      🏥 면책 조항 이미지 생성: {temp_path}")
            print(f"      🏥 이미지 크기: {img_width}x{img_height}, Duration: {duration}초")
            
            # Create ImageClip with explicit duration
            txt_clip = ImageClip(temp_path).with_duration(duration)
            
            # Position at bottom (Raised higher to avoid Shorts UI)
            # VIDEO_HEIGHT - 600 preserves space for title/channel name
            txt_clip = txt_clip.with_position(('center', VIDEO_HEIGHT - 600))
            
            print(f"      🏥 면책 조항 위치: center, {VIDEO_HEIGHT - 600}")
            
            # Use explicit size to ensure proper compositing
            result = CompositeVideoClip([clip, txt_clip], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
            print(f"      🏥 면책 조항 합성 완료!")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add medical disclaimer: {e}")
            print(f"      ❌ 면책 조항 추가 실패: {e}")
            import traceback
            traceback.print_exc()
            return clip

    def _create_summary_card(self, checklist: list, duration: float = None):
        """
        핵심 정보 카드를 생성합니다 (영상 끝에 붙일 독립 클립).
        
        Args:
            checklist: 체크리스트 문자열 리스트 (예: ["✓ 물 많이 마시기", ...])
            duration: 카드 표시 시간 (None이면 config 사용)
            
        Returns:
            ImageClip or None
        """
        # 설정 파일에서 불러오기
        from config.summary_card_config import (
            CARD_DURATION, MAX_ITEMS, FONT_SIZE, LINE_SPACING,
            TEXT_COLOR, TEXT_ALIGN, BG_IMAGE, BG_COLOR, FONT_FILE
        )
        
        if not checklist:
            print(f"      ⚠️ 체크리스트가 비어있어 카드 생성 건너뜀")
            return None
        
        if duration is None:
            duration = CARD_DURATION
        
        try:
            print(f"\n   📋 [핵심 정보 카드 생성]")
            
            # 텍스트 준비 (줄바꿈으로 연결)
            # 긴 줄은 자동 줄바꿈 (최대 15자)
            MAX_LINE_CHARS = 15
            wrapped_lines = []
            for item in checklist[:MAX_ITEMS]:
                if len(item) > MAX_LINE_CHARS:
                    # 공백 기준으로 줄바꿈
                    words = item.split()
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= MAX_LINE_CHARS:
                            current_line = current_line + " " + word if current_line else word
                        else:
                            if current_line:
                                wrapped_lines.append(current_line)
                            current_line = "   " + word  # 들여쓰기
                    if current_line:
                        wrapped_lines.append(current_line)
                else:
                    wrapped_lines.append(item)
            
            card_text = "\n".join(wrapped_lines)
            
            # 폰트 로드
            from pathlib import Path
            if FONT_FILE:
                font_path = Path(__file__).parent.parent / "fonts" / FONT_FILE
                try:
                    font = ImageFont.truetype(str(font_path), FONT_SIZE)
                except:
                    font = ImageFont.truetype(self.font, FONT_SIZE) if self.font else ImageFont.load_default()
            else:
                try:
                    font = ImageFont.truetype(self.font, FONT_SIZE) if self.font else ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
            
            # 텍스트 크기 계산
            dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bbox = dummy_draw.textbbox((0, 0), card_text, font=font, spacing=LINE_SPACING)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 배경 이미지 로드
            if BG_IMAGE:
                bg_image_path = Path(__file__).parent.parent / "assets" / BG_IMAGE
                if bg_image_path.exists():
                    img = Image.open(str(bg_image_path)).convert('RGB')
                else:
                    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
            else:
                img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
            
            draw = ImageDraw.Draw(img)
            
            # 중앙 정렬
            x = (VIDEO_WIDTH - text_width) / 2
            y = (VIDEO_HEIGHT - text_height) / 2
            
            # 텍스트 그리기
            draw.multiline_text((x, y), card_text, font=font, fill=TEXT_COLOR, 
                               spacing=LINE_SPACING, align=TEXT_ALIGN)
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
                img.save(tf.name)
                temp_path = tf.name
            
            print(f"      ✅ 카드 이미지 생성: {temp_path}")
            print(f"      ✅ 체크리스트 {len(checklist[:MAX_ITEMS])}개 항목, Duration: {duration}초")
            
            # ImageClip 생성
            card_clip = ImageClip(temp_path).with_duration(duration)
            
            return card_clip
            
        except Exception as e:
            print(f"      ❌ 핵심 정보 카드 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None


    def _add_subtitle(self, clip, text: str, duration: float):
        """Adds a subtitle overlay to a clip using Pillow for rendering."""
        from config.subtitle_config import (
            get_subtitle_style, is_impact_text, 
            SUBTITLE_Y_POSITION
        )
        
        try:
            text = text.strip()
            if not text:
                return clip
            
            # --- 1. Smart Text Splitting (문장부호 + 길이 기반 분할) ---
            # 목표: 한 화면에 한 줄만 나오도록 적절히 자르기
            
            # 1차: 문장부호로 분리 (. ? ! ,) - 쉼표도 분기점으로 활용
            import re
            # 정규식: 문장부호(.?!,) 뒤의 공백에서 분리, 문장부호는 앞 문장에 포함
            raw_segments = re.split(r'(?<=[.?!,])\s+', text)
            raw_segments = [s.strip() for s in raw_segments if s.strip()]
            
            final_segments = []
            MAX_CHARS = 12  # 한 줄 권장 글자수 (test-channel: 더 짧게 분할)
            
            for seg in raw_segments:
                if len(seg) <= MAX_CHARS + 3:  # 여유 15자 이하
                    final_segments.append(seg)
                else:
                    # 글자수 비율 기반 분할 (어절 경계 유지)
                    words = seg.split()
                    if len(words) <= 2:
                        final_segments.append(seg)
                    else:
                        # 글자수 비율로 분할점 계산
                        total_chars = len(seg.replace(" ", ""))  # 공백 제외 글자수
                        
                        # 2분할 또는 3분할 결정
                        if total_chars <= 25:
                            # 2분할
                            target = total_chars / 2
                            parts = self._split_by_char_ratio(words, [target, total_chars])
                        else:
                            # 3분할
                            target1 = total_chars / 3
                            target2 = target1 * 2
                            parts = self._split_by_char_ratio(words, [target1, target2, total_chars])
                        
                        for p in parts:
                            if p.strip():
                                final_segments.append(p.strip())
            
            if not final_segments:
                return clip

            # --- 2. Proportional Duration Calculation (글자수 비례 시간 배분) ---
            # 공백 제외 글자수 계산 (한글은 글자수 비례가 싱크에 더 정확함)
            segment_lengths = [len(s.replace(" ", "")) for s in final_segments]
            total_length = sum(segment_lengths)
            
            if total_length == 0:
                total_length = 1 # avoid divide by zero
            
            subtitle_clips = []
            current_time = 0
            
            # 스타일은 기본 스타일만 가져오고, 강조 로직은 _create_subtitle_image 내부에서 처리
            style = get_subtitle_style(False) 
            
            for i, sentence in enumerate(final_segments):
                # 비례 배분: (내 글자수 / 전체 글자수) * 전체 시간
                char_ratio = segment_lengths[i] / total_length
                seg_duration = duration * char_ratio
                
                # 최소 시간 보장 (너무 짧은 경우) - 단, 전체 시간이 짧으면 비율대로
                if duration > 1.5 and seg_duration < 0.5:
                     seg_duration = max(0.2, seg_duration)

                # Create image using Pillow (Partial Coloring Logic Inside)
                # [수정] 자막 렌더링 시 쉼표/마침표 제거 (화면에 안 보이게)
                clean_sentence = sentence.replace(',', '').replace('.', '').strip()
                img_path = self._create_subtitle_image(clean_sentence, style)
                
                if img_path and os.path.exists(img_path):
                    txt_clip = ImageClip(img_path)
                    # Fix: Use _set_exact_duration for compatibility
                    txt_clip = self._set_exact_duration(txt_clip, seg_duration)
                    
                    # Fixed position
                    try:
                        txt_clip = txt_clip.with_position(('center', SUBTITLE_Y_POSITION))
                    except AttributeError:
                        txt_clip = txt_clip.set_position(('center', SUBTITLE_Y_POSITION))
                    
                    # Set timing
                    try:
                        txt_clip = txt_clip.with_start(current_time)
                    except AttributeError:
                        txt_clip = txt_clip.set_start(current_time)
                    
                    subtitle_clips.append(txt_clip)
                
                current_time += seg_duration
            
            if subtitle_clips:
                # Clean up temp files later if possible, but for now OS handles tmp
                return CompositeVideoClip([clip] + subtitle_clips)
            return clip
                
        except Exception as e:
            logger.warning(f"Failed to add subtitle: {e}")
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
