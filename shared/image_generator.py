import os
import time
import logging
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from shared.config.model_config import IMAGE_MODEL, IMAGE_FALLBACK_MODEL
from config.image_config import (
    IMAGE_NEGATIVE_PROMPT, IMAGE_MAX_WORKERS,
    IMAGE_SIZE, IMAGE_MAX_RETRIES, IMAGE_RETRY_BASE_DELAY, IMAGE_REQUEST_DELAY
)

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generates images for video scenes using Imagen or Gemini API.
    Supports batch generation for style consistency and cost optimization.
    
    모델 자동 감지:
    - 모델명에 'imagen'이 포함되면 → generate_images() API 사용
    - 그 외 (gemini 등)이면 → generate_content() API 사용
    """
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
        self.style_guide = "simple 2D cartoon, flat colors, thick black outlines, 9:16 aspect ratio vertical, consistent visual style, no text"
        
        # 모델 타입 자동 감지
        self.use_imagen = "imagen" in IMAGE_MODEL.lower()
        self.fallback_used_count = 0  # Fallback 모델 사용 횟수 추적
        self.use_fallback_mode = False  # 메인 모델 실패 시 이후 장면은 Fallback으로 전환
        logger.info(f"ImageGenerator initialized with model: {IMAGE_MODEL} ({'Imagen' if self.use_imagen else 'Gemini'} mode)")
    
    def get_fallback_used_count(self):
        """Return count of how many times fallback model was used."""
        return self.fallback_used_count

    def _generate_with_imagen(self, prompt: str, output_path: str) -> str:
        """Imagen API를 사용한 이미지 생성 (기본 모델)"""
        return self._generate_with_imagen_model(prompt, output_path, IMAGE_MODEL)
    
    def _generate_with_imagen_model(self, prompt: str, output_path: str, model: str) -> str:
        """Imagen API를 사용한 이미지 생성 (지정된 모델)"""
        response = self.client.models.generate_images(
            model=model,
            prompt=prompt,
            config={
                'number_of_images': 1,
                'aspect_ratio': "9:16"
            }
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            return output_path
        else:
            raise Exception(f"No images generated from Imagen API (model: {model})")

    def _generate_with_gemini(self, prompt: str, output_path: str, model: str = None, image_size: str = None) -> str:
        """Gemini API를 사용한 이미지 생성 (generate_content with IMAGE modality)"""
        target_model = model or IMAGE_MODEL
        # image_size는 gemini-3.1 이상만 지원, gemini-2.5는 미지원
        img_config = types.ImageConfig(aspect_ratio="9:16")
        if image_size:
            img_config = types.ImageConfig(aspect_ratio="9:16", image_size=image_size)
        
        response = self.client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=img_config
            )
        )
        
        # Gemini 응답에서 이미지 추출 (Null-safe)
        if not response:
            raise Exception("Gemini API returned empty response")
        
        if not response.candidates:
            raise Exception("Gemini API returned no candidates")
        
        candidate = response.candidates[0]
        if not candidate or not candidate.content:
            raise Exception("Gemini API returned empty candidate content")
        
        if not candidate.content.parts:
            raise Exception("Gemini API returned no content parts")
        
        for part in candidate.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                # base64 디코딩이 필요한 경우
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
                
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                return output_path
        
        raise Exception("No image data found in Gemini API response")

    def generate_image(self, prompt: str, output_path: str, style_guide: str = None):
        """
        Generates an image using Imagen or Gemini API based on model config.
        Falls back to local placeholder if API fails.
        """
        # Ensure .png extension
        if not output_path.endswith('.png'):
            output_path = output_path.replace('.mp4', '.png')
        
        if not self.client:
            logger.error("Gemini client not initialized.")
            return self._create_placeholder(prompt, output_path)

        # Use provided style guide or default
        style = style_guide if style_guide else self.style_guide
        
        # Print the full prompt to terminal
        full_prompt = f"{prompt}, {style}{IMAGE_NEGATIVE_PROMPT}"
        api_type = "Imagen" if self.use_imagen else "Gemini"
        print(f"\n   📝 [이미지 생성 프롬프트] ({api_type})")
        print(f"   {'─'*46}")
        print(f"   모델: {IMAGE_MODEL}")
        print(f"   {full_prompt}")
        print(f"   {'─'*46}\n")
        
        logger.info(f"Generating image for prompt: {prompt[:50]}...")
        try:
            if self.use_imagen:
                result = self._generate_with_imagen(full_prompt, output_path)
            else:
                result = self._generate_with_gemini(full_prompt, output_path)
            
            logger.info(f"Saved generated image to {output_path}")
            print(f"   ✅ 이미지 생성 완료: {output_path}\n")
            return result

        except Exception as e:
            logger.error(f"Error generating image with {api_type}: {e}")
            print(f"\n{'='*50}")
            print(f"  ❌ [에러 발생] {api_type} API 실패")
            print(f"{'='*50}")
            print(f"   에러 내용: {str(e)}")
            print(f"   {'─'*46}")
            print(f"   🔄 [대안 선택] 플레이스홀더 이미지를 로컬에서 생성합니다...")
            print(f"{'='*50}\n")
            return self._create_placeholder(prompt, output_path)

    def _create_placeholder(self, prompt: str, output_path: str):
        """Creates a simple placeholder image when API fails."""
        try:
            width, height = 1080, 1920
            img = Image.new('RGB', (width, height), color=(20, 20, 40))
            d = ImageDraw.Draw(img)
            
            text = f"SCENE IMAGE\n(Placeholder)\n\n{prompt[:80]}..."
            d.text((100, height//2 - 100), text, fill=(255, 255, 255))
            
            img.save(output_path)
            logger.info(f"Saved placeholder image to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            return None

    def _generate_single_image(self, idx: int, prompt: str, output_path: str, style: str, audio_context: str = None):
        """
        Helper method to generate a single image.
        Automatically uses Imagen or Gemini based on model config.
        Retries on 429 errors with exponential backoff.
        Tries fallback model if primary fails.
        """
        enhanced_prompt = f"{prompt}, {style}{IMAGE_NEGATIVE_PROMPT}"
        
        # Fallback 모드가 활성화되었으면 바로 Fallback 모델 사용
        if self.use_fallback_mode and IMAGE_FALLBACK_MODEL:
            current_model = IMAGE_FALLBACK_MODEL
            print(f"\n   📝 [Scene {idx} 이미지 프롬프트] (Fallback 모드)")
            print(f"   {'─'*46}")
            print(f"   모델: {IMAGE_FALLBACK_MODEL} (Fallback 지속)")
            print(f"   {enhanced_prompt}")
            print(f"   {'─'*46}")
            
            try:
                fallback_is_imagen = "imagen" in IMAGE_FALLBACK_MODEL.lower()
                if fallback_is_imagen:
                    self._generate_with_imagen_model(enhanced_prompt, output_path, IMAGE_FALLBACK_MODEL)
                else:
                    fallback_image_size = IMAGE_SIZE if "3." in IMAGE_FALLBACK_MODEL else None
                    self._generate_with_gemini(
                        enhanced_prompt, output_path,
                        model=IMAGE_FALLBACK_MODEL,
                        image_size=fallback_image_size
                    )
                self.fallback_used_count += 1
                return (idx, output_path, True, None)
            except Exception as fallback_error:
                logger.error(f"Fallback model failed for scene {idx}: {fallback_error}")
                return (idx, None, False, f"Fallback: {fallback_error}")
        
        # Print prompt for visibility
        api_type = "Imagen" if self.use_imagen else "Gemini"
        print(f"\n   📝 [Scene {idx} 이미지 프롬프트] ({api_type})")
        print(f"   {'─'*46}")
        print(f"   모델: {IMAGE_MODEL}")
        print(f"   {enhanced_prompt}")
        print(f"   {'─'*46}")
        
        # Try primary model with retry on 429
        for attempt in range(1, IMAGE_MAX_RETRIES + 1):
            try:
                if self.use_imagen:
                    self._generate_with_imagen_model(enhanced_prompt, output_path, IMAGE_MODEL)
                else:
                    self._generate_with_gemini(enhanced_prompt, output_path)
                
                return (idx, output_path, True, None)
                    
            except Exception as primary_error:
                error_str = str(primary_error)
                
                # 429 에러면 지수 백오프 재시도
                if "429" in error_str and attempt < IMAGE_MAX_RETRIES:
                    wait_time = IMAGE_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    print(f"   ⏳ Rate limit 초과, {wait_time}초 후 재시도... ({attempt}/{IMAGE_MAX_RETRIES})")
                    time.sleep(wait_time)
                    continue
                
                logger.error(f"Primary model failed for scene {idx}: {primary_error}")
                
                # Try fallback model if configured
                if IMAGE_FALLBACK_MODEL:
                    print(f"   ⚠️  기본 모델 실패, Fallback 모델({IMAGE_FALLBACK_MODEL}) 시도 중...")
                    print(f"   🔄 이후 장면들도 Fallback 모델로 전환합니다.")
                    try:
                        fallback_is_imagen = "imagen" in IMAGE_FALLBACK_MODEL.lower()
                        if fallback_is_imagen:
                            self._generate_with_imagen_model(enhanced_prompt, output_path, IMAGE_FALLBACK_MODEL)
                        else:
                            fallback_image_size = IMAGE_SIZE if "3." in IMAGE_FALLBACK_MODEL else None
                            self._generate_with_gemini(
                                enhanced_prompt, output_path,
                                model=IMAGE_FALLBACK_MODEL,
                                image_size=fallback_image_size
                            )
                        self.fallback_used_count += 1
                        self.use_fallback_mode = True  # 이후 장면은 Fallback으로 전환
                        print(f"   ✅ Fallback 모델로 성공!")
                        return (idx, output_path, True, None)
                    except Exception as fallback_error:
                        logger.error(f"Fallback model also failed for scene {idx}: {fallback_error}")
                        return (idx, None, False, f"Primary: {primary_error}, Fallback: {fallback_error}")
                else:
                    return (idx, None, False, error_str)

    def generate_images_batch(self, prompts: list, output_dir: str, style_guide: str = None, audio_contexts: list = None, parallel: bool = True, max_workers: int = None):
        """
        Generate multiple images in batch with consistent style.
        Supports both sequential and parallel processing.
        Automatically uses Imagen or Gemini based on model config.
        """
        if not self.client:
            logger.error("Gemini client not initialized.")
            raise Exception("Gemini Client not initialized. Cannot generate images.")
        
        if max_workers is None:
            max_workers = IMAGE_MAX_WORKERS
        
        style = style_guide if style_guide else self.style_guide
        api_type = "Imagen" if self.use_imagen else "Gemini"
        
        print(f"\n   🎨 [배치 이미지 생성 시작] ({api_type})")
        print(f"   모델: {IMAGE_MODEL}")
        print(f"   총 {len(prompts)}개 이미지 생성")
        print(f"   스타일 가이드: {style}")
        print(f"   모드: {'병렬 처리' if parallel else '순차 처리'}")
        if parallel:
            print(f"   동시 작업 수: {max_workers}")
        print(f"   {'─'*46}\n")
        
        generated_paths = [None] * len(prompts)
        completed = 0
        
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(
                        self._generate_single_image,
                        idx + 1,
                        prompt,
                        os.path.join(output_dir, f"scene_{idx + 1}.png"),
                        style,
                        audio_contexts[idx] if audio_contexts and idx < len(audio_contexts) else None
                    ): idx
                    for idx, prompt in enumerate(prompts)
                }
                
                for future in as_completed(future_to_idx):
                    idx, path, success, error = future.result()
                    original_idx = future_to_idx[future]
                    generated_paths[original_idx] = path
                    completed += 1
                    
                    if success:
                        print(f"      ✅ Scene {idx} 완료 ({completed}/{len(prompts)})")
                    else:
                        print(f"      ❌ Scene {idx} 실패: {error}")
                        raise Exception(f"Image generation failed for Scene {idx}: {error}")
        else:
            for idx, prompt in enumerate(prompts, 1):
                # Rate limit 방지를 위한 요청 간 딜레이
                if idx > 1:
                    time.sleep(IMAGE_REQUEST_DELAY)
                
                output_path = os.path.join(output_dir, f"scene_{idx}.png")
                print(f"   [{idx}/{len(prompts)}] 이미지 생성 중...")
                
                audio_ctx = audio_contexts[idx - 1] if audio_contexts and (idx - 1) < len(audio_contexts) else None
                result_idx, path, success, error = self._generate_single_image(
                    idx, prompt, output_path, style, audio_ctx
                )
                generated_paths[idx - 1] = path
                completed += 1
                
                if success:
                    print(f"      ✅ Scene {idx} 완료: {path}")
                else:
                    print(f"      ❌ Scene {idx} 실패: {error}")
                    raise Exception(f"Image generation failed for Scene {idx}: {error}")
        
        print(f"\n   ✅ 배치 생성 완료: {completed}/{len(prompts)}개 성공\n")
        return generated_paths

    def generate_placeholder_batch(self, prompts: list, output_dir: str):
        """
        Uses a single pre-generated test image from assets/test_images/.
        The same image is copied for all scenes (flexible for any scene count).
        """
        import shutil
        from pathlib import Path
        
        print(f"\n   🧪 [테스트 모드] 미리 생성된 테스트 이미지 사용")
        print(f"   총 {len(prompts)}개 장면\n")
        
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        test_image_path = project_root / "assets" / "test_images" / "test_placeholder.png"
        
        if not test_image_path.exists():
            print(f"      ❌ 테스트 이미지 없음: {test_image_path}")
            print(f"      💡 python3 assets/test_images/generate_test_images.py 실행 필요")
            return [None] * len(prompts)
        
        generated_paths = []
        for idx in range(1, len(prompts) + 1):
            output_path = os.path.join(output_dir, f"scene_{idx}.png")
            shutil.copy(test_image_path, output_path)
            generated_paths.append(output_path)
            print(f"      ✅ Scene {idx}: 테스트 이미지 사용")
                
        print(f"\n   ✅ 테스트 이미지 적용 완료\n")
        return generated_paths

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = ImageGenerator()
    print(f"Model: {IMAGE_MODEL}")
    print(f"Mode: {'Imagen' if gen.use_imagen else 'Gemini'}")
