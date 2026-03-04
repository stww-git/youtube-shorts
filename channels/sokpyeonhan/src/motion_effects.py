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

    def compose_video(self, scenes: List[Dict], audio_path: str = None, output_path: str = None, video_title: str = None, summary_checklist: list = None, summary_title: str = "", summary_card_duration: float = 3.0, include_disclaimer: bool = False, bgm_enabled: bool = False, bgm_volume: float = 0.1, bgm_file: str = None, subtitle_mode: str = "static", typing_speed: float = 0.20, single_font_size: int = 140, static_font_size: int = 80, ai_subtitle_effects: bool = False, color_keywords: dict = None, ken_burns_effect: bool = True, ken_burns_zoom: float = 0.05, summary_card_show_title: bool = True):
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
                
                # Image files: Apply Ken Burns effect or static
                if asset_path.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    if ken_burns_effect:
                        clip = self._apply_ken_burns_effect(asset_path, duration, zoom_intensity=ken_burns_zoom)
                    else:
                        clip = self._apply_static_image(asset_path, duration)
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

                if text and clip:
                    # AI 효과 데이터가 있으면 전달
                    scene_effect = scene.get('subtitle_effect', None) if ai_subtitle_effects else None
                    clip = self._add_subtitle(clip, text, duration, subtitle_mode=subtitle_mode, typing_speed=typing_speed, single_font_size=single_font_size, static_font_size=static_font_size, scene_effect=scene_effect, color_keywords=color_keywords)
                
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
            
            # === Title + Summary Card 순서 제어 ===
            # summary_card_show_title=False: 제목을 먼저 씨우고 → 핵심 카드를 뒤에 붙임 (카드에 제목 없음)
            # summary_card_show_title=True:  핵심 카드를 먼저 붙이고 → 제목을 전체에 씨움 (카드에도 제목 있음)
            
            if not summary_card_show_title and video_title:
                # 제목을 먼저 본편에만 적용
                final_video = self._apply_title_overlay(final_video, video_title)
                
                # 그 다음 핵심 정보 카드 추가 (제목 없이)
                if summary_checklist:
                    print(f"   📋 핵심 정보 카드 추가 중...")
                    summary_card = self._create_summary_card(summary_checklist, duration=summary_card_duration, summary_title=summary_title)
                    if summary_card:
                        final_video = concatenate_videoclips([final_video, summary_card], method="compose")
                        print(f"   ✅ 핵심 카드 추가 완료 (최종 길이: {final_video.duration:.2f}초)")
            else:
                # 핵심 정보 카드 먼저 추가
                if summary_checklist:
                    print(f"   📋 핵심 정보 카드 추가 중...")
                    summary_card = self._create_summary_card(summary_checklist, duration=summary_card_duration, summary_title=summary_title)
                    if summary_card:
                        final_video = concatenate_videoclips([final_video, summary_card], method="compose")
                        print(f"   ✅ 핵심 카드 추가 완료 (최종 길이: {final_video.duration:.2f}초)")
                
                # 그 다음 제목 오버레이 (전체에 적용)
                if video_title:
                    final_video = self._apply_title_overlay(final_video, video_title)
            
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

    def _apply_ken_burns_effect(self, image_path: str, duration: float, zoom_intensity: float = 0.05):
        """
        Applies Ken Burns (slow zoom) effect to a static image.
        Creates a gentle zoom from 1.0x to (1.0 + zoom_intensity)x over the duration.
        
        Args:
            image_path: Path to the image file
            duration: Duration of the clip
            zoom_intensity: Zoom strength (0.03=subtle, 0.05=normal, 0.10=strong)
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
        
        # Apply zoom effect using configurable intensity
        def zoom_func(t):
            progress = min(t / duration, 1.0)  # Clamp to 0-1
            return 1.0 + zoom_intensity * progress  # Zoom from 1.0x to (1.0 + zoom_intensity)x
        
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
    
    def _apply_static_image(self, image_path: str, duration: float):
        """
        Loads a static image and fits it to 1080x1920 without any animation.
        """
        img_clip = ImageClip(image_path)
        target_width, target_height = VIDEO_WIDTH, VIDEO_HEIGHT
        
        # Scale to fit
        scale_h = target_height / img_clip.h
        scale_w = target_width / img_clip.w
        scale = max(scale_h, scale_w)
        
        new_height = int(img_clip.h * scale)
        img_clip = img_clip.resized(height=new_height)
        
        # Crop to center
        if img_clip.w > target_width or img_clip.h > target_height:
            img_clip = img_clip.cropped(
                x_center=img_clip.w / 2,
                y_center=img_clip.h / 2,
                width=target_width,
                height=target_height
            )
        
        img_clip = self._set_exact_duration(img_clip, duration)
        return img_clip
    
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
    
    def _create_subtitle_image(self, text, style, highlight_word_idx=-1):
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
                SUBTITLE_MAX_WIDTH,
                POPIN_HIGHLIGHT_COLOR
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
            word_counter = 0  # 전체 단어 인덱스 추적 (하이라이트용)
            
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
                # word_color_func가 있으면 우선 사용 (Scene 6 전용 등)
                word_color_func = style.get('word_color_func')
                if word_color_func:
                    color = word_color_func(word, text_color)
                elif not style.get('skip_keyword_color'):
                    keyword_color = get_keyword_color(word, text_color)
                    # Pop-in 하이라이트: skip_keyword_color가 아닐 때만
                    if highlight_word_idx >= 0 and word_counter == highlight_word_idx and keyword_color == text_color:
                        color = POPIN_HIGHLIGHT_COLOR
                    else:
                        color = keyword_color
                else:
                    color = text_color
                word_counter += 1
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

    def _apply_title_overlay(self, final_video, video_title):
        """영상 위에 제목 텍스트 + 검은 배경 오버레이를 추가합니다."""
        first_sentence = self._extract_first_sentence(video_title)
        print(f"   📌 제목 추가 중: {first_sentence[:30]}...")
        
        from config.title_config import TITLE_FONT_PATH, TITLE_LINE_COLORS, TITLE_TOP_MARGIN, TITLE_BG_TOP_MARGIN, get_adaptive_title_style
        TOP_MARGIN = TITLE_BG_TOP_MARGIN
        title_font = TITLE_FONT_PATH
        title_text = first_sentence
        
        font_size, line_height_factor = get_adaptive_title_style(len(title_text))
        
        use_pillow_title = True
        
        if use_pillow_title:
            try:
                title_image_path = create_title_image(
                    text=title_text,
                    font_size=font_size,
                    font_path=title_font,
                    line_colors=TITLE_LINE_COLORS
                )
                
                title_clip = ImageClip(title_image_path)
                title_clip = self._set_exact_duration(title_clip, final_video.duration)
                
                from PIL import Image as PILImage
                with PILImage.open(title_image_path) as img:
                    title_img_height = img.height
                
                print(f"      🎨 Pillow 방식 사용 (자간: -5px)")
                
            except Exception as e:
                logger.warning(f"Pillow title failed: {e}. Falling back to TextClip.")
                use_pillow_title = False
        
        if not use_pillow_title:
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
            title_img_height = None
            print(f"      📝 TextClip 방식 사용 (기본 자간)")
        
        if use_pillow_title and title_img_height:
            bg_height = int(TOP_MARGIN + title_img_height + 80)
        else:
            avg_chars_per_line = 10
            num_lines = max(1, (len(title_text) + avg_chars_per_line - 1) // avg_chars_per_line)
            line_height = int(font_size * line_height_factor)
            text_height = num_lines * line_height
            bg_height = int(TOP_MARGIN + text_height + 80)
        
        bg_height = max(bg_height, 220)
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
        
        text_y_position = TITLE_TOP_MARGIN + 40
        
        try:
            title_clip = title_clip.with_position(('center', text_y_position))
        except AttributeError:
            title_clip = title_clip.set_position(('center', text_y_position))
        
        final_video = CompositeVideoClip([final_video, bg_clip, title_clip])
        print(f"   ✅ 제목 추가 완료 (검정 배경 포함)\n")
        
        return final_video

    def _create_summary_card(self, checklist: list, duration: float = None, summary_title: str = ""):
        """
        핵심 정보 카드를 생성합니다 (영상 끝에 붙일 독립 클립).
        
        Args:
            checklist: 체크리스트 문자열 리스트 (예: ["• 물 많이 마시기", ...])
            duration: 카드 표시 시간 (None이면 config 사용)
            
        Returns:
            ImageClip or None
        """
        # 설정 파일에서 불러오기
        from config.summary_card_config import (
            CARD_DURATION, MAX_ITEMS, FONT_SIZE, LINE_SPACING,
            TEXT_COLOR, TEXT_ALIGN, BG_IMAGE, BG_COLOR, FONT_FILE,
            TEXT_STROKE_COLOR, TEXT_STROKE_WIDTH
        )
        
        if not checklist:
            print(f"      ⚠️ 체크리스트가 비어있어 카드 생성 건너뜀")
            return None
        
        if duration is None:
            duration = CARD_DURATION
        
        try:
            print(f"\n   📋 [핵심 정보 카드 생성]")
            
            # 좌우 여백 설정
            MARGIN_X = 60
            max_text_width = VIDEO_WIDTH - (MARGIN_X * 2)
            
            # 폰트 로드 함수
            from pathlib import Path
            def _load_font(size):
                if FONT_FILE:
                    font_path = Path(__file__).parent.parent / "fonts" / FONT_FILE
                    try:
                        return ImageFont.truetype(str(font_path), size)
                    except:
                        pass
                try:
                    return ImageFont.truetype(self.font, size) if self.font else ImageFont.load_default()
                except:
                    return ImageFont.load_default()
            
            font_size = FONT_SIZE
            font = _load_font(font_size)
            
            # 텍스트 줄바꿈: 실제 픽셀 너비 기준으로 줄바꿈
            def _wrap_text_by_width(items, fnt, max_w):
                """실제 렌더링 너비 기준으로 텍스트 줄바꿈"""
                dummy = ImageDraw.Draw(Image.new('RGB', (1, 1)))
                result = []
                for item in items:
                    # 한 줄에 들어가는지 확인
                    bbox = dummy.textbbox((0, 0), item, font=fnt)
                    if (bbox[2] - bbox[0]) <= max_w:
                        result.append(item)
                    else:
                        # 글자 단위로 줄바꿈 (한국어는 공백이 적으므로)
                        current = ""
                        for char in item:
                            test = current + char
                            bbox = dummy.textbbox((0, 0), test, font=fnt)
                            if (bbox[2] - bbox[0]) <= max_w:
                                current = test
                            else:
                                if current:
                                    result.append(current)
                                current = "  " + char  # 들여쓰기
                        if current:
                            result.append(current)
                return result
            
            wrapped_lines = _wrap_text_by_width(checklist[:MAX_ITEMS], font, max_text_width)
            card_text = "\n".join(wrapped_lines)
            
            # 텍스트 크기 계산 → 넘치면 폰트 축소
            dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bbox = dummy_draw.textbbox((0, 0), card_text, font=font, spacing=LINE_SPACING)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 텍스트가 화면 높이의 85%를 넘으면 폰트 크기 축소
            max_text_height = int(VIDEO_HEIGHT * 0.85)
            while (text_width > max_text_width or text_height > max_text_height) and font_size > 30:
                font_size -= 4
                font = _load_font(font_size)
                wrapped_lines = _wrap_text_by_width(checklist[:MAX_ITEMS], font, max_text_width)
                card_text = "\n".join(wrapped_lines)
                bbox = dummy_draw.textbbox((0, 0), card_text, font=font, spacing=LINE_SPACING)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            
            if font_size != FONT_SIZE:
                print(f"      ℹ️ 폰트 크기 자동 조정: {FONT_SIZE} → {font_size}")
            
            # 배경 이미지 로드 (VIDEO_WIDTH x VIDEO_HEIGHT로 리사이즈)
            if BG_IMAGE:
                bg_image_path = Path(__file__).parent.parent / "assets" / BG_IMAGE
                if bg_image_path.exists():
                    img = Image.open(str(bg_image_path)).convert('RGB')
                    if img.size != (VIDEO_WIDTH, VIDEO_HEIGHT):
                        img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS)
                else:
                    print(f"      ⚠️ 배경 이미지 없음: {bg_image_path}")
                    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
            else:
                img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
            
            draw = ImageDraw.Draw(img)
            
            # === 제목 렌더링 ===
            title_height = 0
            TITLE_BOTTOM_MARGIN = 30
            if summary_title:
                title_font_size = int(font_size * 1.3)
                title_font = _load_font(title_font_size)
                
                title_bbox = draw.textbbox((0, 0), summary_title, font=title_font)
                title_text_width = title_bbox[2] - title_bbox[0]
                title_text_height = title_bbox[3] - title_bbox[1]
                title_height = title_text_height + TITLE_BOTTOM_MARGIN
                
                title_x = max(MARGIN_X, (VIDEO_WIDTH - title_text_width) / 2)
                title_y = max(40, (VIDEO_HEIGHT - text_height - title_height) / 2)
                
                title_stroke = {}
                if TEXT_STROKE_WIDTH > 0:
                    title_stroke['stroke_width'] = TEXT_STROKE_WIDTH + 1
                    title_stroke['stroke_fill'] = TEXT_STROKE_COLOR
                draw.text((title_x, title_y), summary_title, font=title_font, fill="#FFFFFF", **title_stroke)
                print(f"      📌 카드 제목: {summary_title}")
            
            # 중앙 정렬 (좌우 여백 보장) - 제목 높이만큼 아래로
            x = max(MARGIN_X, (VIDEO_WIDTH - text_width) / 2)
            if summary_title:
                y = title_y + title_height
            else:
                y = (VIDEO_HEIGHT - text_height) / 2
            
            # 텍스트 그리기 (외곽선 포함)
            stroke_kwargs = {}
            if TEXT_STROKE_WIDTH > 0:
                stroke_kwargs['stroke_width'] = TEXT_STROKE_WIDTH
                stroke_kwargs['stroke_fill'] = TEXT_STROKE_COLOR
            draw.multiline_text((x, y), card_text, font=font, fill=TEXT_COLOR, 
                               spacing=LINE_SPACING, align=TEXT_ALIGN, **stroke_kwargs)
            
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

    def _merge_short_words(self, words, min_chars=2):
        """2글자 이하의 짧은 어절을 인접 어절과 병합합니다."""
        if len(words) <= 1:
            return words
        
        merged = []
        i = 0
        while i < len(words):
            word = words[i]
            # 현재 단어가 짧으면 다음 단어와 합침
            if len(word) <= min_chars and i + 1 < len(words):
                merged.append(word + ' ' + words[i + 1])
                i += 2
            # 현재 단어가 짧고 마지막이면 이전 단어와 합침
            elif len(word) <= min_chars and merged:
                merged[-1] = merged[-1] + ' ' + word
                i += 1
            else:
                merged.append(word)
                i += 1
        
        return merged

    def _get_ai_color(self, word_text, color_keywords):
        """color_keywords에서 어절 텍스트의 색상을 조회합니다."""
        if not color_keywords:
            return 'white'
        for color, keywords in color_keywords.items():
            for kw in keywords:
                if kw in word_text or word_text in kw:
                    return color
        return 'white'

    def _add_subtitle_with_ai_effects(self, clip, text, duration, style, scene_effect, single_font_size, static_font_size, typing_speed, color_keywords=None):
        """AI가 지정한 어절/효과 데이터로 자막을 렌더링합니다."""
        import math
        from config.subtitle_config import SUBTITLE_Y_POSITION
        
        display_mode = scene_effect.get('display', 'single')
        ai_words = scene_effect.get('words', [])
        
        if not ai_words:
            return clip
        
        # 폰트 크기: display 모드에 따라 분리
        render_style = dict(style)
        if display_mode == 'static':
            render_style['font_size'] = static_font_size
        else:
            render_style['font_size'] = single_font_size
        
        # static 모드: 문장 전체를 한 번에 표시
        if display_mode == 'static':
            word_text = ai_words[0].get('text', text)
            word_effect = ai_words[0].get('effect', None)
            
            # AI 색상 적용
            word_render_style = dict(render_style)
            word_render_style['max_width'] = 700  # 줄바꿈 유도 (좋아요 한 번만 / 눌러주세요)
            word_render_style['skip_keyword_color'] = True  # 기존 키워드 색상 비활성화
            
            # Scene 6 전용 3색 매핑 (좋아요 CTA)
            if '좋아요' in word_text:
                from config.subtitle_config import get_scene6_word_color
                word_render_style['word_color_func'] = get_scene6_word_color
            else:
                ai_color = self._get_ai_color(word_text, color_keywords)
                if ai_color != 'white':
                    word_render_style['text_color'] = ai_color
            
            img_path = self._create_subtitle_image(word_text, word_render_style)
            if img_path and os.path.exists(img_path):
                sub_clip = ImageClip(img_path)
                sub_clip = self._set_exact_duration(sub_clip, duration)
                
                # 효과 적용 (Scene 6은 2회 bounce)
                if word_effect and duration >= 0.15:
                    bounce_count = 2 if '좋아요' in word_text else 1
                    sub_clip = self._apply_word_effect(sub_clip, word_effect, duration, bounce_count=bounce_count)
                
                try:
                    sub_clip = sub_clip.with_position(('center', SUBTITLE_Y_POSITION))
                except AttributeError:
                    sub_clip = sub_clip.set_position(('center', SUBTITLE_Y_POSITION))
                
                return CompositeVideoClip([clip, sub_clip])
            return clip
        
        # single 모드: 어절 단위로 순차 표시
        num_words = len(ai_words)
        if num_words == 0:
            return clip
        
        typing_ratio = min(0.95, typing_speed * num_words)
        typing_duration = duration * typing_ratio
        hold_duration = duration - typing_duration
        interval = typing_duration / num_words if num_words > 0 else typing_duration
        
        animated_clips = []
        
        for w_idx, word_info in enumerate(ai_words):
            word_text = word_info.get('text', '')
            word_effect = word_info.get('effect', None)
            
            if not word_text:
                continue
            
            # AI 색상 적용
            word_render_style = dict(render_style)
            word_render_style['skip_keyword_color'] = True  # 기존 키워드 색상 비활성화
            ai_color = self._get_ai_color(word_text, color_keywords)
            if ai_color != 'white':
                word_render_style['text_color'] = ai_color
            
            img_path = self._create_subtitle_image(word_text, word_render_style, highlight_word_idx=-1)
            if img_path and os.path.exists(img_path):
                partial_clip = ImageClip(img_path)
                
                # 마지막 어절은 hold 시간 추가
                if w_idx == num_words - 1:
                    partial_dur = hold_duration + interval
                else:
                    partial_dur = interval
                
                partial_clip = self._set_exact_duration(partial_clip, partial_dur)
                
                # 효과 적용
                if word_effect and partial_dur >= 0.15:
                    partial_clip = self._apply_word_effect(partial_clip, word_effect, partial_dur)
                
                try:
                    partial_clip = partial_clip.with_position(('center', SUBTITLE_Y_POSITION))
                except AttributeError:
                    partial_clip = partial_clip.set_position(('center', SUBTITLE_Y_POSITION))
                
                partial_start = w_idx * interval
                try:
                    partial_clip = partial_clip.with_start(partial_start)
                except AttributeError:
                    partial_clip = partial_clip.set_start(partial_start)
                
                animated_clips.append(partial_clip)
        
        if animated_clips:
            return CompositeVideoClip([clip] + animated_clips)
        return clip
    
    def _apply_word_effect(self, clip, effect_type, clip_duration, bounce_count=1):
        """어절 클립에 bounce 효과를 적용합니다."""
        single_anim = min(0.2, clip_duration * 0.4)
        anim_duration = single_anim * bounce_count  # 각 bounce에 충분한 시간 확보
        
        if effect_type == "bounce":
            # 바운스 팝: 80% → 110% → 100% (bounce_count회 반복)
            def make_bounce_func(anim_dur, count):
                def bounce_func(t):
                    single = anim_dur / count
                    cycle_t = t % single if t < anim_dur else single
                    if cycle_t < single * 0.6:
                        progress = cycle_t / (single * 0.6)
                        return 0.8 + 0.3 * progress
                    elif cycle_t < single:
                        progress = (cycle_t - single * 0.6) / (single * 0.4)
                        return 1.1 - 0.1 * progress
                    return 1.0
                return bounce_func
            clip = clip.resized(make_bounce_func(anim_duration, bounce_count))
        
        return clip

    def _add_subtitle(self, clip, text: str, duration: float, subtitle_mode: str = "static", typing_speed: float = 0.20, single_font_size: int = 140, static_font_size: int = 80, scene_effect: dict = None, color_keywords: dict = None):
        """Adds a subtitle overlay to a clip using Pillow for rendering."""
        from config.subtitle_config import (
            get_subtitle_style, is_impact_text, 
            SUBTITLE_Y_POSITION
        )
        
        try:
            text = text.strip()
            if not text:
                return clip
            
            # AI 효과 모드: scene_effect가 있으면 AI가 지정한 어절/효과 사용
            if scene_effect:
                from config.subtitle_config import get_subtitle_style, SUBTITLE_Y_POSITION
                style = get_subtitle_style(False)  # AI 모드: 기본 흰색, color_keywords로 색상 적용
                return self._add_subtitle_with_ai_effects(clip, text, duration, style, scene_effect, single_font_size, static_font_size, typing_speed, color_keywords=color_keywords)
            
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
                img_path = self._create_subtitle_image(sentence, style)
                
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
                    # 동적 자막용: 원본 텍스트 저장
                    txt_clip._subtitle_text = sentence
                
                current_time += seg_duration
            
            if subtitle_clips:
                if subtitle_mode in ("accumulate", "single"):
                    # Pop-in 효과: 어절 단위로 순차적으로 나타나는 애니메이션
                    animated_subtitle_clips = []
                    
                    # single 모드: 큰 폰트 스타일 생성
                    if subtitle_mode == "single":
                        single_style = dict(style)
                        single_style['font_size'] = single_font_size
                    
                    for sub_clip_info in subtitle_clips:
                        seg_text = sub_clip_info._subtitle_text if hasattr(sub_clip_info, '_subtitle_text') else ''
                        seg_start = sub_clip_info.start if hasattr(sub_clip_info, 'start') else 0
                        seg_dur = sub_clip_info.duration if hasattr(sub_clip_info, 'duration') else 0
                        
                        words = seg_text.split() if seg_text else []
                        
                        # single 모드: 짧은 어절 병합 (2글자 이하 → 인접 어절과 합침)
                        if subtitle_mode == "single" and len(words) > 1:
                            words = self._merge_short_words(words)
                        
                        if len(words) <= 1 or seg_dur < 0.5:
                            animated_subtitle_clips.append(sub_clip_info)
                        else:
                            typing_ratio = min(0.95, typing_speed * len(words))
                            typing_duration = seg_dur * typing_ratio
                            hold_duration = seg_dur - typing_duration
                            
                            interval = typing_duration / len(words) if len(words) > 0 else typing_duration
                            
                            for w_idx in range(len(words)):
                                if subtitle_mode == "accumulate":
                                    # 누적형: 어절이 계속 쌓임
                                    partial_text = ' '.join(words[:w_idx + 1])
                                    highlight_idx = w_idx
                                    current_style = style
                                else:
                                    # single: 한 어절만 표시 (큰 폰트)
                                    partial_text = words[w_idx]
                                    highlight_idx = -1
                                    current_style = single_style
                                
                                partial_img_path = self._create_subtitle_image(partial_text, current_style, highlight_word_idx=highlight_idx)
                                if partial_img_path and os.path.exists(partial_img_path):
                                    partial_clip = ImageClip(partial_img_path)
                                    
                                    if w_idx == len(words) - 1:
                                        partial_dur = hold_duration + interval
                                    else:
                                        partial_dur = interval
                                    
                                    partial_clip = self._set_exact_duration(partial_clip, partial_dur)
                                    
                                    # single 모드: 스케일 팝 / 바운스 팝 효과 적용
                                    if subtitle_mode == "single" and partial_dur >= 0.15:
                                        anim_duration = min(0.2, partial_dur * 0.4)
                                        if w_idx % 2 == 0:
                                            # 스케일 팝: 80% → 100%
                                            def make_scale_func(anim_dur):
                                                def scale_func(t):
                                                    if t < anim_dur:
                                                        progress = t / anim_dur
                                                        return 0.8 + 0.2 * progress
                                                    return 1.0
                                                return scale_func
                                            partial_clip = partial_clip.resized(make_scale_func(anim_duration))
                                        else:
                                            # 바운스 팝: 80% → 110% → 100%
                                            def make_bounce_func(anim_dur):
                                                def bounce_func(t):
                                                    if t < anim_dur * 0.6:
                                                        progress = t / (anim_dur * 0.6)
                                                        return 0.8 + 0.3 * progress  # 80% → 110%
                                                    elif t < anim_dur:
                                                        progress = (t - anim_dur * 0.6) / (anim_dur * 0.4)
                                                        return 1.1 - 0.1 * progress  # 110% → 100%
                                                    return 1.0
                                                return bounce_func
                                            partial_clip = partial_clip.resized(make_bounce_func(anim_duration))
                                    
                                    try:
                                        partial_clip = partial_clip.with_position(('center', SUBTITLE_Y_POSITION))
                                    except AttributeError:
                                        partial_clip = partial_clip.set_position(('center', SUBTITLE_Y_POSITION))
                                    
                                    partial_start = seg_start + (w_idx * interval)
                                    try:
                                        partial_clip = partial_clip.with_start(partial_start)
                                    except AttributeError:
                                        partial_clip = partial_clip.set_start(partial_start)
                                    
                                    animated_subtitle_clips.append(partial_clip)
                    
                    if animated_subtitle_clips:
                        return CompositeVideoClip([clip] + animated_subtitle_clips)
                else:
                    # static: 기존 통짜 방식
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
                title_clip = title_clip.with_position(('center', 0.13), relative=True)
            except AttributeError:
                title_clip = title_clip.set_position(('center', 0.13), relative=True)
            
            return CompositeVideoClip([clip, title_clip])
        except Exception as e:
            logger.warning(f"Failed to add title: {e}")
            return clip

if __name__ == "__main__":
    composer = MotionEffectsComposer()
    # composer.compose_video(...)
