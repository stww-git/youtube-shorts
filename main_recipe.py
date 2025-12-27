"""
레시피 기반 YouTube Shorts 자동 생성 시스템

10000recipe.com에서 레시피를 가져와 쇼츠 영상을 생성합니다.
"""

import os
import sys
import time
import re
import json
import warnings
from datetime import datetime

# Suppress ALL warnings before importing other modules
warnings.filterwarnings('ignore')
import logging
logging.captureWarnings(True)

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress urllib3 warnings
try:
    import urllib3
    urllib3.disable_warnings()
except:
    pass

from dotenv import load_dotenv

from src.recipe_crawler import RecipeCrawler
from src.recipe_title_generator import RecipeTitleGenerator
from src.recipe_script_generator import RecipeScriptGenerator
from src.image_prompt_generator import ImagePromptGenerator
from src.image_generator import ImageGenerator
from src.audio_generator import AudioGenerator
from src.motion_effects import MotionEffectsComposer

# Load environment variables
load_dotenv()

def print_header(text):
    """Print a styled header."""
    print(f"\n{'🍳'*25}")
    print(f"  {text}")
    print(f"{'🍳'*25}")

def print_step(step_num, total_steps, title, status="🔄 진행 중"):
    """Print a step indicator with progress bar."""
    progress = "█" * step_num + "░" * (total_steps - step_num)
    percent = int((step_num / total_steps) * 100)
    
    print(f"\n{'='*60}")
    print(f"  📍 STEP {step_num}/{total_steps}  [{progress}] {percent}%")
    print(f"{'='*60}")
    print(f"  📌 {title}")
    print(f"  ⏳ {status}")
    print(f"{'='*60}")

def print_step_complete(step_num, total_steps, title):
    """Print step completion."""
    print(f"\n{'─'*60}")
    print(f"  ✅ STEP {step_num}/{total_steps} 완료: {title}")
    print(f"{'─'*60}")

def print_substep(text):
    """Print a sub-step or detail."""
    print(f"   ▶ {text}")

def print_success(text):
    """Print a success message."""
    print(f"   ✅ {text}")

def print_warning(text):
    """Print a warning message."""
    print(f"   ⚠️  {text}")

def print_error(text):
    """Print an error message."""
    print(f"   ❌ {text}")

def print_info(text):
    """Print an info message."""
    print(f"   ℹ️  {text}")

def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that are not safe for filenames."""
    filename = re.sub(r'[<>:"/\\|?*#!@$%^&()\[\]{}+=~`\';,]', '', filename)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename.strip(' .')
    if len(filename) > 80:
        filename = filename[:80]
    return filename

def create_output_folder(recipe_title: str) -> str:
    """Create output folder with recipe title and date."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(recipe_title)
    
    if not safe_title or len(safe_title.strip()) == 0:
        safe_title = "recipe"
    
    folder_name = f"{safe_title}_{date_str}"
    
    if not os.path.exists("output"):
        os.makedirs("output", exist_ok=True)
    
    output_dir = os.path.join("output", folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def check_environment():
    """Check if necessary API keys are present."""
    required_keys = ["GOOGLE_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"❌ Error: Missing API keys in .env file: {', '.join(missing_keys)}")
        sys.exit(1)
    print_success("Environment check passed. API keys loaded.")

def main():
    print_header("🍳 YouTube Shorts 자동 생성 시스템 (Recipe-Based)")
    
    check_environment()
    
    # Initialize Modules
    print_substep("Initializing modules...")
    crawler = RecipeCrawler()
    title_gen = RecipeTitleGenerator()
    script_gen = RecipeScriptGenerator()
    image_prompt_gen = ImagePromptGenerator()
    image_gen = ImageGenerator()
    audio_gen = AudioGenerator()
    composer = MotionEffectsComposer()
    print_success("All modules initialized.")
    
    # ==========================================
    # Step 1: Get Recipe from 10000recipe.com
    # ==========================================
    print_step(1, 6, "레시피 선택", "🍲 10000recipe.com 크롤링 중")
    
    recipe = crawler.get_next_recipe()
    
    if not recipe:
        print_error("사용 가능한 레시피가 없습니다.")
        return
    
    original_title = recipe.get('title', '요리 레시피')
    print_success(f"레시피 선택 완료!")
    print(f"\n   📌 원본 레시피: {original_title}")
    print(f"   📦 재료: {len(recipe.get('ingredients', []))}개")
    print(f"   📋 조리단계: {len(recipe.get('steps', []))}개")
    
    # ==========================================
    # Step 2: Script Generation (대본 먼저 생성)
    # ==========================================
    print_step(2, 6, "대본 생성", "✍️ Gemini AI 작성 중")
    
    script_json = script_gen.generate_script(recipe)
    
    if not script_json:
        print_error("대본 생성 실패!")
        return
    
    # Parse JSON
    try:
        json_match = re.search(r'\{[\s\S]*"scenes"[\s\S]*\}', script_json, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            script_data = json.loads(json_str)
        else:
            json_str = script_json.replace("```json", "").replace("```", "").strip()
            script_data = json.loads(json_str)
        
        scenes = script_data.get('scenes', [])
        
        if not scenes:
            print_error("No scenes found in the script.")
            print(script_json)
            return
            
    except Exception as e:
        print_error(f"Failed to parse script JSON: {e}")
        print(script_json)
        return

    print_success(f"Script generated with {len(scenes)} scenes:")
    for scene in scenes:
        print(f"      Scene {scene['scene_id']}: {scene['audio_text'][:40]}... ({scene.get('duration', 3)}s)")
    print("")

    # ==========================================
    # Step 3: Generate Video Title (대본 기반)
    # ==========================================
    print_step(3, 6, "제목 생성", "✨ 대본 기반 제목 생성 중")
    
    video_title = title_gen.generate_title(recipe, scenes)
    print(f"\n   📌 생성된 제목: {video_title}")
    
    # Create output folder
    output_dir = create_output_folder(video_title)
    print(f"   📁 출력 폴더 생성: {output_dir}")
    
    # Save title and script to file
    script_file = os.path.join(output_dir, "script.txt")
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(f"[제목]\n{video_title}\n\n")
        f.write(f"[대본]\n")
        for scene in scenes:
            f.write(f"{scene['scene_id']}. {scene['audio_text']}\n")
    print(f"   📝 대본/제목 저장: script.txt")

    # ==========================================
    # Step 4: Audio Generation (통합 생성 + Silence 분할)
    # ==========================================
    print_step(4, 6, "나레이션 오디오 생성", "🎤 Gemini TTS 통합 생성 중")
    
    try:
        # 개별 장면별 오디오 생성 (싱크 정확도 향상)
        # Batch 생성 대신 개별 생성을 사용하여 파일 분할 오류 방지
        print(f"   🔊 개별 장면 오디오 생성 시작 (총 {len(scenes)}개)...")
        
        audio_paths = []
        for idx, scene in enumerate(scenes):
            scene_id = scene['scene_id']
            text = scene['audio_text']
            
            # [Naturalness Fix]
            # 자막에는 마침표가 없어도 자연스럽지만, TTS는 마침표가 있어야 문장의 끝으로 인식하고 톤을 내립니다.
            # 따라서 TTS 생성을 위한 텍스트에는 문장부호가 없으면 마침표를 임시로 추가합니다.
            tts_text = text.strip()
            if tts_text and not tts_text.endswith(('.', '?', '!')):
                tts_text += '.'
            
            # 파일명: audio_scene_1.wav
            filename = f"audio_scene_{scene_id}.wav"
            filepath = os.path.join(output_dir, filename)
            
            print(f"      Scene {scene_id} 오디오 생성 중... (TTS 입력: {tts_text})")
            generated_path = audio_gen.generate_speech(tts_text, filepath)
            
            if generated_path and os.path.exists(generated_path):
                audio_paths.append(generated_path)
                
                # Update scene info immediately
                scene['audio_path'] = generated_path
                scene['duration'] = audio_gen.get_audio_duration(generated_path)
            else:
                raise Exception(f"Scene {scene_id} Audio Generation Failed")
            
            # API Rate Limit 방지를 위한 짧은 대기
            time.sleep(1)

        print_success(f"모든 오디오 생성 완료: {len(audio_paths)}/{len(scenes)}개")
        total_duration = sum(s['duration'] for s in scenes)
        print(f"   📏 실제 전체 영상 길이: {total_duration:.2f}초\n")
        
    except Exception as e:
        print_error(f"오디오 생성 실패: {str(e)}")
        raise

    # ==========================================
    # Step 5: Image Generation
    # ==========================================
    print_step(5, 6, "이미지 생성", "🎨 Gemini + Imagen 생성 중")
    
    # Step 4a: Generate English Image Prompts
    print_substep("Step 4a: 영어 이미지 프롬프트 생성 중...")
    image_prompts_json = image_prompt_gen.generate_image_prompts(video_title, scenes)
    
    try:
        json_match = re.search(r'\{[\s\S]*"global_visual_style"[\s\S]*"scenes"[\s\S]*\}', image_prompts_json, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            prompts_data = json.loads(json_str)
        else:
            json_str = image_prompts_json.replace("```json", "").replace("```", "").strip()
            prompts_data = json.loads(json_str)
        
        global_visual_style = prompts_data.get('global_visual_style', '')
        prompt_scenes = prompts_data.get('scenes', [])
        
        # Merge visual descriptions into scenes
        for ps in prompt_scenes:
            sid = ps.get('scene_id', 0)
            for scene in scenes:
                if scene.get('scene_id') == sid:
                    scene['visual_description'] = ps.get('visual_description', '')
                    break
        
        print_success(f"이미지 프롬프트 생성 완료!")
        print(f"\n   🎨 통합 비주얼 스타일: {global_visual_style[:60]}...")
        for scene in scenes:
            print(f"      Scene {scene['scene_id']}: {scene.get('visual_description', '')[:50]}...")
        print("")
        
    except Exception as e:
        print_error(f"Failed to parse image prompts JSON: {e}")
        print(image_prompts_json)
        return
    
    # Step 4b: Generate Images
    print_substep("Step 4b: Imagen으로 이미지 생성 중...")
    
    visual_descriptions = [scene.get('visual_description', '') for scene in scenes]
    
    try:
        generated_paths = image_gen.generate_images_batch(
            prompts=visual_descriptions,
            output_dir=output_dir,
            style_guide=global_visual_style
        )
    except Exception as e:
        print_error("이미지 생성 중 치명적 오류 발생!")
        print(f"   ❌ {str(e)}")
        print("\n   ⛔ 프로젝트 실행을 중단합니다.")
        return
    
    # Assign generated paths to scenes
    for idx, scene in enumerate(scenes):
        if idx < len(generated_paths) and generated_paths[idx]:
            scene['image_path'] = generated_paths[idx]
            print(f"      ✅ Scene {scene['scene_id']}: {generated_paths[idx]}")
        else:
            print(f"      ❌ Scene {scene['scene_id']}: Failed")
        
    # ==========================================
    # Step 6: Final Composition
    # ==========================================
    print_step(6, 6, "최종 영상 합성", "🎞️ MoviePy 합성 중")
    
    # 파일명을 영상 제목과 동일하게 설정
    safe_video_title = sanitize_filename(video_title)
    final_output = os.path.join(output_dir, f"{safe_video_title}.mp4")
    result = composer.compose_video(scenes, audio_path=None, output_path=final_output, video_title=video_title)
    
    if not result:
        print_error("영상 합성 실패!")
        print_info(f"이미지와 오디오는 {output_dir} 폴더에 저장되어 있습니다.")
        return
    
    print_success(f"Final video saved to {final_output}")
    
    # Mark recipe as used
    crawler.mark_as_used(
        recipe['recipe_id'], 
        video_title, 
        recipe.get('category', 'best'),
        recipe.get('url')
    )
    
    # ==========================================
    # Done!
    # ==========================================
    print_header("🎉 작업 완료!")
    print(f"""
   📁 출력 폴더: {output_dir}
   📁 Output Files:
      - Video:  {final_output}
      - Images: {output_dir}/scene_*.png
      - Audio:  {output_dir}/audio_scene_*.mp3
   
   📊 Gemini API 호출 횟수: {title_gen.get_api_call_count() + script_gen.get_api_call_count() + image_prompt_gen.get_api_call_count()}회
   
   ℹ️  다음 단계: '{final_output}'를 YouTube에 업로드하세요!
""")

if __name__ == "__main__":
    main()
