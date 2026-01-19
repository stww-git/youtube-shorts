
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
    create_output_folder, sanitize_filename, format_steps
)
from core.channel_manager import (
    get_channel_config, get_channel_prompts, get_upload_config, get_refresh_token, get_output_dir
)
from core.prompt_logger import reset_prompt_logger, get_prompt_logger

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

    def run(self, test_mode: bool = False, image_parallel: bool = True, upload_to_youtube: bool = False, channel_id: str = None, allow_fallback: bool = False, privacy_status: str = "private", include_summary_card: bool = False, include_disclaimer: bool = False, bgm_enabled: bool = False, bgm_volume: float = 0.1, bgm_file: str = None):
        """
        Execute the video generation pipeline.
        
        Args:
            test_mode: If True, uses placeholder images instead of generating new ones via API.
            image_parallel: If True, generates images in parallel (faster). If False, sequential (safer).
            upload_to_youtube: If True, uploads the generated video to YouTube.
            channel_id: Target channel folder name (e.g., 'sokpyeonhan'). Use default if None.
            allow_fallback: If True, uses fallback methods (e.g. gTTS) on failure. If False, raises exception.
            privacy_status: YouTube privacy status ('public', 'unlisted', 'private'). From main.py settings.
        """
        
        # Load channel-specific prompts if channel_id is specified
        channel_prompts = None
        if channel_id:
            channel_prompts = get_channel_prompts(channel_id)
        # ==========================================
        # Step 1: Get Recipe from 10000recipe.com
        # ==========================================
        print_step(1, 7, "레시피 선택", "🍲 10000recipe.com 크롤링 중")
        
        # Kick이 있는 레시피를 찾을 때까지 반복
        MAX_RECIPE_ATTEMPTS = 5  # 최대 5개 레시피 시도
        recipe = None
        kick_analysis = None
        
        for attempt in range(1, MAX_RECIPE_ATTEMPTS + 1):
            recipe = self.crawler.get_next_recipe()
            
            if not recipe:
                print_error("사용 가능한 레시피가 없습니다.")
                raise Exception("사용 가능한 레시피가 없습니다.")
            
            original_title = recipe.get('title', '요리 레시피')
            print_success(f"레시피 선택 완료! (시도 {attempt}/{MAX_RECIPE_ATTEMPTS})")
            print(f"\n   📌 원본 레시피: {original_title}")
            print(f"   📦 재료: {len(recipe.get('ingredients', []))}개")
            print(f"   📋 조리단계: {len(recipe.get('steps', []))}개")
            
            # ==========================================
            # Step 2: Kick 분석 (신뢰도 체크)
            # ==========================================
            print_step(2, 7, "Kick 분석", "🔍 핵심 비법 존재 여부 확인 중")
            
            kick_analysis = self.script_gen.analyze_kick(recipe, min_confidence=5)
            
            if kick_analysis.get("has_kick", True):
                print_success(f"Kick 확인: {kick_analysis.get('kick_candidate', 'N/A')}")
                break  # Kick 있으면 루프 탈출
            else:
                print_warning(f"이 레시피에는 명확한 Kick이 없습니다. 다음 레시피 시도...")
                print_info(f"   이유: {kick_analysis.get('reason', 'N/A')}")
                print_info(f"   신뢰도: {kick_analysis.get('confidence', 0)}/10")
                # Mark recipe as used (skipped) - use correct method name
                self.crawler.mark_as_used(
                    recipe_id=recipe.get('recipe_id', ''),
                    title=original_title,
                    category="skipped"
                )
                if attempt == MAX_RECIPE_ATTEMPTS:
                    raise Exception(f"{MAX_RECIPE_ATTEMPTS}개 레시피 모두 Kick 부재로 스킵됨")
        
        # Initialize prompt debug logger
        debug_logger = reset_prompt_logger()
        debug_logger.log_raw_data({
            "recipe_id": recipe.get('recipe_id', ''),
            "title": original_title,
            "ingredients": recipe.get('ingredients', []),
            "steps": recipe.get('steps', []),
        }, data_type="레시피")
        
        # Log Kick analysis
        debug_logger.log_raw_data({
            "kick_analysis": kick_analysis
        }, data_type="Kick 분석")
        
        # ==========================================
        # Step 3: Script Generation (대본 생성)
        # ==========================================
        print_step(3, 7, "대본 생성", "✍️ Gemini AI 작성 중")
        
        # Kick 분석 결과를 대본 생성에 전달
        kick_candidate = kick_analysis.get("kick_candidate", "")
        script_json = self.script_gen.generate_script(recipe, kick=kick_candidate)
        
        if not script_json:
            print_error("대본 생성 실패!")
            raise Exception("대본 생성 실패!")
        
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
                raise Exception("No scenes found in the script.")
                
        except Exception as e:
            print_error(f"Failed to parse script JSON: {e}")
            print(script_json)
            raise Exception(f"Failed to parse script JSON: {e}")

        print_success(f"Script generated with {len(scenes)} scenes:")
        for scene in scenes:
            print(f"      Scene {scene['scene_id']}: {scene['audio_text'][:40]}... ({scene.get('duration', 3)}s)")
        print("")
        
        # Log script generation - actual input to prompt
        # Script prompt uses: title + format_steps(steps)
        actual_steps_text = format_steps(recipe.get('steps', []))
        raw_steps_json = json.dumps(recipe.get('steps', []), ensure_ascii=False, indent=2)
        script_input = f"[title]\n{original_title}\n\n[steps - 원본 (JSON)]\n{raw_steps_json}\n\n[steps - 프롬프트에 전달된 값 (format_steps 결과)]\n{actual_steps_text}"
        script_output = json.dumps(script_data, ensure_ascii=False, indent=2)
        debug_logger.log_prompt_step(3, "대본 생성", script_input, "(SCRIPT_GENERATION_PROMPT 사용 - title, steps 변수 전달)", script_output, "SCRIPT_GENERATION_PROMPT")

        # ==========================================
        # Step 4: Generate Video Title (대본 기반)
        # ==========================================
        print_step(4, 7, "제목 생성", "✨ 대본 기반 제목 생성 중")
        
        video_title = self.title_gen.generate_title(recipe, scenes)
        print(f"\n   📌 생성된 제목: {video_title}")
        
        # Log title generation - actual input to prompt
        # Title prompt uses: title + script_content (from scenes)
        script_lines = [f"{scene['scene_id']}번: {scene['audio_text']}" for scene in scenes]
        script_content = "\n".join(script_lines)
        title_input = f"[title]\n{original_title}\n\n[script_content]\n{script_content}"
        debug_logger.log_prompt_step(4, "제목 생성", title_input, "(TITLE_GENERATION_PROMPT 사용 - title, script_content 변수 전달)", video_title, "TITLE_GENERATION_PROMPT")
        
        # Create output folder (채널별 출력 경로 사용)
        channel_output_base = str(get_output_dir(channel_id)) if channel_id else None
        output_dir = create_output_folder(video_title, base_output_dir=channel_output_base)
        print(f"   📁 출력 폴더 생성: {output_dir}")
        
        # Set output dir for prompt debug logger
        debug_logger.set_output_dir(output_dir)
        
        # Save title and script to file
        script_file = os.path.join(output_dir, "script.txt")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(f"[제목]\n{video_title}\n\n")
            f.write(f"[대본]\n")
            for scene in scenes:
                f.write(f"{scene['scene_id']}. {scene['audio_text']}\n")
        print(f"   📝 대본/제목 저장: script.txt")

        # ==========================================
        # Step 5: Audio Generation (통합 생성 + Silence 분할)
        # ==========================================
        print_step(5, 7, "나레이션 오디오 생성", "🎤 Gemini TTS 통합 생성 중")
        
        try:
            # 전체 대본을 한 번에 TTS 생성 후 분할 (톤 일관성 및 자연스러움 확보)
            audio_paths = self.audio_gen.generate_speech_batch(scenes, output_dir, allow_fallback=allow_fallback)
        
            print_success(f"모든 오디오 생성 완료: {len(audio_paths)}/{len(scenes)}개")
            total_duration = sum(s['duration'] for s in scenes)
            print(f"   📏 예상 전체 영상 길이: {total_duration:.2f}초\n")
            
        except Exception as e:
            print_error(f"오디오 생성 실패: {str(e)}")
            raise

        # ==========================================
        # Step 6: Image Generation
        # ==========================================
        print_step(6, 7, "이미지 생성", "🎨 Gemini + Imagen 생성 중")
        
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
                
                # Log image prompt generation
                script_text_for_log = "\n".join([f"Scene {s['scene_id']}: {s['audio_text']}" for s in scenes])
                image_prompt_input = f"[title]\n{video_title}\n\n[script_text]\n{script_text_for_log}"
                image_prompt_output = f"[global_visual_style]\n{global_visual_style}\n\n[scenes]\n" + "\n".join([
                    f"Scene {s['scene_id']}: {s.get('visual_description', '')}" for s in scenes
                ])
                debug_logger.log_prompt_step(5, "이미지 프롬프트 생성", image_prompt_input, "(IMAGE_GENERATION_PROMPT 사용)", image_prompt_output, "IMAGE_GENERATION_PROMPT")
                
            except Exception as e:
                print_error(f"Failed to parse image prompts JSON: {e}")
                print(image_prompts_json)
                raise Exception(f"Failed to parse image prompts JSON: {e}")
            
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
                raise
        
        # Assign generated paths to scenes
        for idx, scene in enumerate(scenes):
            if idx < len(generated_paths) and generated_paths[idx]:
                scene['image_path'] = generated_paths[idx]
                print(f"      ✅ Scene {scene['scene_id']}: {generated_paths[idx]}")
            else:
                print(f"      ❌ Scene {scene['scene_id']}: Failed")
            
        # ==========================================
        # Step 7: Final Composition
        # ==========================================
        print_step(7, 7, "최종 영상 합성", "🎞️ MoviePy 합성 중")
        
        # Generate summary checklist if enabled
        summary_checklist = None
        if include_summary_card:
            # Construct full recipe content for better summary
            steps_text = format_steps(recipe.get('steps', []))
            # Handle ingredients as list of dicts: [{"name": "계란", "amount": "3개"}, ...]
            ingredients_list = recipe.get('ingredients', [])
            if ingredients_list and isinstance(ingredients_list[0], dict):
                ingredients_text = ", ".join([f"{i.get('name', '')} {i.get('amount', '')}".strip() for i in ingredients_list])
            elif isinstance(ingredients_list, list):
                ingredients_text = ", ".join(ingredients_list)
            else:
                ingredients_text = str(ingredients_list)
            
            full_content = f"""
[요리 제목] {recipe.get('title', '')}

[재료 목록]
{ingredients_text}

[조리 순서]
{steps_text}
"""
            # Add tips if available (assuming 'tips' key exists, adjust if needed)
            if recipe.get('tips'):
                full_content += f"\n[요리 팁]\n{recipe['tips']}"

            # Extract Kick (Scene 7's audio_text) for summary card alignment
            kick = ""
            for scene in scenes:
                if scene.get('scene_id') == 7:
                    kick = scene.get('audio_text', '')
                    break
            
            summary_checklist = self.script_gen.generate_summary(full_content, kick=kick)
            
            # Log summary card generation
            if summary_checklist:
                debug_logger.log_prompt_step(7, "핵심 정보 카드 생성", full_content, "(SUMMARY_GENERATION_PROMPT 사용)", str(summary_checklist), "SUMMARY_GENERATION_PROMPT")
        
        # 파일명을 영상 제목과 동일하게 설정
        safe_video_title = sanitize_filename(video_title)
        final_output = os.path.join(output_dir, f"{safe_video_title}.mp4")
        
        # Save prompt debug log before rendering
        debug_logger.save()
        
        result = self.composer.compose_video(scenes, audio_path=None, output_path=final_output, video_title=video_title, summary_checklist=summary_checklist, include_disclaimer=include_disclaimer, bgm_enabled=bgm_enabled, bgm_volume=bgm_volume, bgm_file=bgm_file)
        
        if not result:
            print_error("영상 합성 실패!")
            print_info(f"이미지와 오디오는 {output_dir} 폴더에 저장되어 있습니다.")
            raise Exception("영상 합성 실패!")
        
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
                    # privacy_status는 main.py에서 전달받은 값 사용 (파라미터로 전달됨)
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
                    else:
                        raise Exception("업로드 후 video_id가 반환되지 않았습니다.")
                except Exception as e:
                    print_error(f"YouTube 업로드 실패: {e}")
                    raise

        # ==========================================
        # Done!
        # ==========================================
        print_header("🎉 작업 완료!")
        
        # 사용된 모델 정보 가져오기
        from config.model_config import TEXT_MODEL, IMAGE_MODEL, IMAGE_FALLBACK_MODEL, TTS_MODEL
        
        print(f"""
       📁 출력 폴더: {output_dir}
       📁 Output Files:
          - Video:  {final_output}
          - Images: {output_dir}/scene_*.png
          - Audio:  {output_dir}/audio_scene_*.wav
       
       📊 API 호출 횟수: {self.title_gen.get_api_call_count() + self.script_gen.get_api_call_count() + self.image_prompt_gen.get_api_call_count()}회
       
       🤖 사용된 모델:
          - 텍스트 생성: {TEXT_MODEL}
          - 이미지 생성: {IMAGE_MODEL}
          - 이미지 대안: {IMAGE_FALLBACK_MODEL or '없음'} (사용: {self.image_gen.get_fallback_used_count()}회)
          - TTS: {TTS_MODEL}
       
       ℹ️  다음 단계: '{final_output}'를 확인하세요!
    """)
