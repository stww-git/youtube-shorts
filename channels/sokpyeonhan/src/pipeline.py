
import os
import re
import json
import logging
from crawler import RecipeCrawler
from title_generator import RecipeTitleGenerator
from script_generator import RecipeScriptGenerator
from image_prompt_generator import ImagePromptGenerator
from image_generator import ImageGenerator
from audio_generator import AudioGenerator
from motion_effects import MotionEffectsComposer
from core.utils import (
    print_header, print_step, print_substep, print_success, 
    print_warning, print_error, print_info, 
    create_output_folder, sanitize_filename
)
from core.channel_manager import (
    get_channel_config, get_channel_prompts, get_upload_config, get_refresh_token, get_output_dir
)

logger = logging.getLogger(__name__)

class RecipeVideoPipeline:
    """
    Orchestrates the entire process of creating a YouTube Short from a recipe.
    """
    
    def __init__(self):
        print_substep("Initializing modules...")
        self.crawler = RecipeCrawler()
        self.title_gen = RecipeTitleGenerator()
        self.script_gen = RecipeScriptGenerator()
        self.image_prompt_gen = ImagePromptGenerator()
        self.image_gen = ImageGenerator()
        self.audio_gen = AudioGenerator()
        self.composer = MotionEffectsComposer()
        print_success("All modules initialized.")

    def run(self, test_mode: bool = False, image_parallel: bool = True, upload_to_youtube: bool = False, channel_id: str = None):
        """
        Execute the video generation pipeline.
        
        Args:
            test_mode: If True, uses placeholder images instead of generating new ones via API.
            image_parallel: If True, generates images in parallel (faster). If False, sequential (safer).
            upload_to_youtube: If True, uploads the generated video to YouTube.
            channel_id: Target channel folder name (e.g., 'sokpyeonhan'). Use default if None.
        """
        
        # Load channel-specific prompts if channel_id is specified
        channel_prompts = None
        if channel_id:
            channel_prompts = get_channel_prompts(channel_id)
        # ==========================================
        # Step 1: Get Recipe from 10000recipe.com
        # ==========================================
        print_step(1, 6, "레시피 선택", "🍲 10000recipe.com 크롤링 중")
        
        recipe = self.crawler.get_next_recipe()
        
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
        
        script_json = self.script_gen.generate_script(recipe)
        
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
        
        video_title = self.title_gen.generate_title(recipe, scenes)
        print(f"\n   📌 생성된 제목: {video_title}")
        
        # Create output folder (채널별 출력 경로 사용)
        channel_output_base = str(get_output_dir(channel_id)) if channel_id else None
        output_dir = create_output_folder(video_title, base_output_dir=channel_output_base)
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
            # 전체 대본을 한 번에 TTS 생성 후 분할 (톤 일관성 및 자연스러움 확보)
            audio_paths = self.audio_gen.generate_speech_batch(scenes, output_dir)
        
            print_success(f"모든 오디오 생성 완료: {len(audio_paths)}/{len(scenes)}개")
            total_duration = sum(s['duration'] for s in scenes)
            print(f"   📏 예상 전체 영상 길이: {total_duration:.2f}초\n")
            
        except Exception as e:
            print_error(f"오디오 생성 실패: {str(e)}")
            raise

        # ==========================================
        # Step 5: Image Generation
        # ==========================================
        print_step(5, 6, "이미지 생성", "🎨 Gemini + Imagen 생성 중")
        
        if test_mode:
            # Test Mode: Skip Prompt Generation & Imagen
            print_substep("Step 4a: 영어 이미지 프롬프트 생성 (테스트 모드: 생략)")
            print_substep("Step 4b: Imagen으로 이미지 생성 (테스트 모드: 플레이스홀더 사용)")
            
            # Use simple prompts for placeholders
            placeholder_prompts = [f"Scene {s['scene_id']}: {s['audio_text'][:20]}..." for s in scenes]
            generated_paths = self.image_gen.generate_placeholder_batch(placeholder_prompts, output_dir)
            
            # Fill empty descriptions for consistency
            for scene in scenes:
                scene['visual_description'] = "(Test Mode Placeholder)"
            global_visual_style = "Test Mode Style"
            
        else:
            # Step 4a: Generate English Image Prompts
            print_substep("Step 4a: 영어 이미지 프롬프트 생성 중...")
            image_prompts_json = self.image_prompt_gen.generate_image_prompts(video_title, scenes)
        
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
                generated_paths = self.image_gen.generate_images_batch(
                    prompts=visual_descriptions,
                    output_dir=output_dir,
                    style_guide=global_visual_style,
                    parallel=image_parallel
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
        result = self.composer.compose_video(scenes, audio_path=None, output_path=final_output, video_title=video_title)
        
        if not result:
            print_error("영상 합성 실패!")
            print_info(f"이미지와 오디오는 {output_dir} 폴더에 저장되어 있습니다.")
            return
        
        print_success(f"Final video saved to {final_output}")
        
        # Mark recipe as used
        self.crawler.mark_as_used(
            recipe['recipe_id'], 
            video_title, 
            recipe.get('category', 'best'),
            recipe.get('url')
        )
        
        if result and upload_to_youtube:
            print_step(7, 7, "유튜브 업로드", "🚀 YouTube에 업로드 중")
            
            client_id = os.getenv("CLIENT_ID")
            client_secret = os.getenv("CLIENT_SECRET")
            
            # Get refresh token from channel config or fallback to env
            refresh_token = None
            upload_config = {}
            
            if channel_id:
                refresh_token = get_refresh_token(channel_id)
                upload_config = get_upload_config(channel_id)
            
            if not refresh_token:
                refresh_token = os.getenv("REFRESH_TOKEN")
            
            if not all([client_id, client_secret, refresh_token]):
                print_error("업로드 불가: CLIENT_ID, CLIENT_SECRET 또는 REFRESH_TOKEN 환경변수가 없습니다.")
            else:
                try:
                    from core.upload.youtube_uploader import YouTubeUploader
                    from config.upload_config import (
                        UPLOAD_TITLE_FORMAT as DEFAULT_TITLE_FORMAT,
                        UPLOAD_DESCRIPTION_TEMPLATE as DEFAULT_DESCRIPTION,
                        DEFAULT_PRIVACY_STATUS, MADE_FOR_KIDS
                    )
                    
                    # client_secrets.json 파일 경로
                    client_secrets_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'client_secrets.json')
                    if not os.path.exists(client_secrets_file):
                        client_secrets_file = os.path.join(os.getcwd(), 'client_secrets.json')
                    
                    # refresh_token을 반환하는 함수 생성
                    def get_token():
                        return refresh_token
                    
                    uploader = YouTubeUploader(client_secrets_file, get_refresh_token_func=get_token)
                    
                    # Use channel-specific config or fallback to defaults
                    title_format = upload_config.get('title_format', DEFAULT_TITLE_FORMAT)
                    description_template = upload_config.get('description', DEFAULT_DESCRIPTION)
                    privacy_status = upload_config.get('privacy_status', DEFAULT_PRIVACY_STATUS)
                    made_for_kids = upload_config.get('made_for_kids', MADE_FOR_KIDS)
                    tags = upload_config.get('tags', [])
                    category_id = upload_config.get('category_id', '22')
                    
                    # 제목과 설명 구성
                    upload_title = title_format.format(
                        title=video_title,
                        category=recipe.get('category', '요리')
                    )
                    
                    upload_description = description_template.format(
                        title=video_title,
                        original_title=recipe.get('title'),
                        url=recipe.get('url', '')
                    ) if description_template else ""
                    
                    video_id = uploader.upload_video(
                        final_output, 
                        upload_title, 
                        upload_description,
                        category_id=category_id,
                        privacy_status=privacy_status,
                        made_for_kids=made_for_kids,
                        keywords=tags
                    )
                    
                    if video_id:
                        print_success(f"YouTube 업로드 성공! Video ID: {video_id}")
                        print(f"   🔗 링크: https://youtube.com/shorts/{video_id}")
                except Exception as e:
                    print_error(f"YouTube 업로드 실패: {e}")

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
       
       📊 Gemini API 호출 횟수: {self.title_gen.get_api_call_count() + self.script_gen.get_api_call_count() + self.image_prompt_gen.get_api_call_count()}회
       
       ℹ️  다음 단계: '{final_output}'를 확인하세요!
    """)
