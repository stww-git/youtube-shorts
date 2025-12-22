import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from src.config import IMAGE_MODEL, IMAGE_NEGATIVE_PROMPT, IMAGE_MAX_WORKERS

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generates images for video scenes using Imagen API or local placeholder.
    Supports batch generation for style consistency and cost optimization.
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found.")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.style_guide = "high quality, cinematic lighting, 9:16 aspect ratio vertical, consistent visual style"

    def generate_image(self, prompt: str, output_path: str, style_guide: str = None):
        """
        Generates an image using Imagen API.
        Falls back to local placeholder if API fails.
        
        Args:
            prompt: Description of the image to generate
            output_path: Path to save the generated image (.png)
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
        print(f"\n   📝 [이미지 생성 프롬프트]")
        print(f"   {'─'*46}")
        print(f"   {full_prompt}")
        print(f"   {'─'*46}\n")
        
        logger.info(f"Generating image for prompt: {prompt[:50]}...")
        try:
            response = self.client.models.generate_images(
                model=IMAGE_MODEL,
                prompt=full_prompt,
                config={
                    'number_of_images': 1,
                    'aspect_ratio': "9:16"
                }
            )
            
            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"Saved generated image to {output_path}")
                print(f"   ✅ 이미지 생성 완료: {output_path}\n")
                return output_path
            else:
                logger.error("No images generated.")
                print(f"\n{'='*50}")
                print(f"  ⚠️  [경고] 이미지 생성 실패 (응답 없음)")
                print(f"{'='*50}")
                print(f"   🔄 [대안 선택] 플레이스홀더 이미지를 생성합니다...")
                print(f"{'='*50}\n")
                return self._create_placeholder(prompt, output_path)

        except Exception as e:
            logger.error(f"Error generating image with Imagen: {e}")
            print(f"\n{'='*50}")
            print(f"  ❌ [에러 발생] Imagen API 실패")
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
        Helper method to generate a single image (for parallel processing).
        Note: audio_context parameter kept for API compatibility but not used.
              visual_description (prompt) is already in English from script_generator.
        """
        try:
            # Use visual_description directly (already English from script_generator)
            enhanced_prompt = f"{prompt}, {style}{IMAGE_NEGATIVE_PROMPT}"
            
            # Print prompt for visibility
            print(f"\n   📝 [Scene {idx} 이미지 프롬프트]")
            print(f"   {'─'*46}")
            print(f"   {enhanced_prompt}")
            print(f"   {'─'*46}")
            
            response = self.client.models.generate_images(
                model=IMAGE_MODEL,
                prompt=enhanced_prompt,
                config={
                    'number_of_images': 1,
                    'aspect_ratio': "9:16"
                }
            )
            
            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                return (idx, output_path, True, None)
            else:
                logger.warning(f"No image generated for scene {idx}")
                # placeholder = self._create_placeholder(prompt, output_path)
                # ERROR: Do not create placeholder if user wants to stop on failure
                return (idx, None, False, "No image in response")
                
        except Exception as e:
            logger.error(f"Error generating image for scene {idx}: {e}")
            # placeholder = self._create_placeholder(prompt, output_path)
            # ERROR: Do not create placeholder
            return (idx, None, False, str(e))

    def generate_images_batch(self, prompts: list, output_dir: str, style_guide: str = None, audio_contexts: list = None, parallel: bool = True, max_workers: int = None):
        """
        Generate multiple images in batch with consistent style.
        Supports both sequential and parallel processing.
        
        **배치 방식의 이점:**
        1. **스타일 일관성**: 모든 이미지에 동일한 스타일 가이드 적용
        2. **병렬 처리**: 여러 이미지를 동시에 생성하여 시간 단축 (parallel=True)
        3. **에러 처리**: 일괄 처리로 에러 핸들링 용이
        4. **진행 상황**: 전체 진행 상황을 한 화면에서 확인
        
        Args:
            prompts: List of prompt strings for each scene
            output_dir: Directory to save all images
            style_guide: Optional style guide to apply to all images
            audio_contexts: Optional list of audio text for each scene (for better image matching)
            parallel: If True, generate images in parallel (faster)
            max_workers: Maximum number of parallel workers (default: 3)
        
        Returns:
            List of generated image paths (in order)
        """
        if not self.client:
            logger.error("Gemini client not initialized.")
            raise Exception("Gemini Client not initialized. Cannot generate images.")
        
        # config에서 기본값 사용
        if max_workers is None:
            max_workers = IMAGE_MAX_WORKERS
        
        style = style_guide if style_guide else self.style_guide
        
        print(f"\n   🎨 [배치 이미지 생성 시작]")
        print(f"   총 {len(prompts)}개 이미지 생성")
        print(f"   스타일 가이드: {style}")
        print(f"   모드: {'병렬 처리' if parallel else '순차 처리'}")
        if parallel:
            print(f"   동시 작업 수: {max_workers}")
        print(f"   {'─'*46}\n")
        
        generated_paths = [None] * len(prompts)
        completed = 0
        
        if parallel:
            # 병렬 처리 모드
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 모든 작업 제출
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
                
                # 완료된 작업 처리
                for future in as_completed(future_to_idx):
                    idx, path, success, error = future.result()
                    original_idx = future_to_idx[future]
                    generated_paths[original_idx] = path
                    completed += 1
                    
                    if success:
                        print(f"      ✅ Scene {idx} 완료 ({completed}/{len(prompts)})")
                    else:
                        print(f"      ❌ Scene {idx} 실패: {error}")
                        # STOP IMMEDIATELY on failure
                        raise Exception(f"Image generation failed for Scene {idx}: {error}")
        else:
            # 순차 처리 모드 (기존 방식)
            for idx, prompt in enumerate(prompts, 1):
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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    gen = ImageGenerator()
    # gen.generate_image("A futuristic city cyberpunk style", "test_img.png")
