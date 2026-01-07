import os
import logging
import wave
import tempfile
import time
from gtts import gTTS
from google import genai
from google.genai import types
from src.config.model_config import TTS_MODEL, MAX_RETRIES, RETRY_DELAY
from src.config.audio_config import TTS_VOICE_NAME

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found.")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def get_audio_duration(self, audio_path: str) -> float:
        """Get the duration of an audio file in seconds."""
        try:
            import wave
            with wave.open(audio_path, 'rb') as audio_file:
                frames = audio_file.getnframes()
                rate = audio_file.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception:
            # Fallback: try with moviepy
            try:
                from moviepy import AudioFileClip
                audio = AudioFileClip(audio_path)
                duration = audio.duration
                audio.close()
                return duration
            except Exception as e:
                logger.error(f"Failed to get audio duration: {e}")
                return 3.0  # Default fallback

    def _save_wav_file(self, filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """Save PCM audio data to WAV file."""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)

    def _convert_wav_to_mp3(self, wav_path: str, mp3_path: str):
        """Convert WAV file to MP3 using pydub (requires ffmpeg)."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3")
            return True
        except ImportError:
            logger.warning("pydub not installed, skipping MP3 conversion")
            return False
        except Exception as e:
            logger.warning(f"MP3 conversion failed: {e}, using WAV instead")
            return False

    def generate_speech(self, text: str, output_path: str, voice: str = None):
        """
        Generate speech using Gemini TTS API.
        
        Args:
            text: Text to convert to speech
            output_path: Output file path (will be saved as MP3 or WAV)
            voice: Voice name for Gemini TTS (default: from config)
        """
        voice = voice or TTS_VOICE_NAME
        logger.info(f"Generating speech for: {text[:20]}...")
        print(f"\n   🎤 [오디오 생성 시작]")
        print(f"   텍스트: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        # Try Gemini TTS with retry logic
        if self.client:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    if attempt > 1:
                        print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                    
                    print(f"   방법: Gemini TTS ({TTS_MODEL})")
                    if attempt == 1:
                        print(f"   ℹ️  Voice: {voice}\n")
                    
                    # Pass plain text without style instructions
                    tts_input = text
                    
                    response = self.client.models.generate_content(
                        model=TTS_MODEL,
                        contents=tts_input,
                        config=types.GenerateContentConfig(
                            response_modalities=["AUDIO"],
                            speech_config=types.SpeechConfig(
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=voice,
                                    )
                                )
                            ),
                        )
                    )
                    
                    # Extract audio data
                    if (response.candidates and 
                        response.candidates[0].content.parts and 
                        response.candidates[0].content.parts[0].inline_data):
                        
                        audio_data = response.candidates[0].content.parts[0].inline_data.data
                        
                        # Save as WAV first (PCM format)
                        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                        temp_wav_path = temp_wav.name
                        temp_wav.close()
                        
                        self._save_wav_file(temp_wav_path, audio_data)
                        
                        # Convert to MP3 if possible, otherwise use WAV
                        if output_path.endswith('.mp3'):
                            if self._convert_wav_to_mp3(temp_wav_path, output_path):
                                os.unlink(temp_wav_path)
                                logger.info(f"Saved Gemini TTS audio to {output_path}")
                                print(f"   ✅ Gemini TTS 오디오 생성 완료: {output_path}\n")
                                return output_path
                            else:
                                # Fallback to WAV
                                wav_path = output_path.replace('.mp3', '.wav')
                                os.rename(temp_wav_path, wav_path)
                                logger.info(f"Saved Gemini TTS audio as WAV: {wav_path}")
                                print(f"   ✅ Gemini TTS 오디오 생성 완료 (WAV): {wav_path}\n")
                                print(f"   ℹ️  MP3 변환 실패, WAV 형식으로 저장되었습니다.\n")
                                return wav_path
                        else:
                            # Already WAV format
                            os.rename(temp_wav_path, output_path)
                            logger.info(f"Saved Gemini TTS audio to {output_path}")
                            print(f"   ✅ Gemini TTS 오디오 생성 완료: {output_path}\n")
                            return output_path
                    else:
                        raise ValueError("No audio data in response")
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # Retry for ALL errors
                    if attempt < MAX_RETRIES:
                        logger.warning(f"Gemini TTS failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                        print(f"\n   ⚠️  [에러 발생] 재시도 대기 중... ({RETRY_DELAY}초)")
                        print(f"   원인: {error_str[:80]}...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        # All retries exhausted - raise error to stop project
                        logger.error(f"Gemini TTS failed after {MAX_RETRIES} attempts: {e}")
                        
                        print(f"\n{'❌'*25}")
                        print(f"  ❌ [치명적 에러] Gemini TTS 생성 실패")
                        print(f"{'❌'*25}")
                        print(f"   {MAX_RETRIES}번 재시도 모두 실패")
                        print(f"   원인: {error_str}")
                        print(f"   텍스트: {text[:50]}...")
                        print(f"{'❌'*25}")
                        print(f"   ⛔ 프로젝트 실행을 중단합니다.")
                        print(f"{'❌'*25}\n")
                        
                        raise Exception(f"Gemini TTS failed after {MAX_RETRIES} retries: {error_str}")

    def generate_speech_batch(self, scenes: list, output_dir: str, voice: str = None):
        """
        전체 대본을 한 번에 TTS 생성 후 silence 기반으로 분할.
        일관된 톤과 자연스러운 억양을 유지합니다.
        
        Args:
            scenes: 장면 목록 [{"scene_id": 1, "audio_text": "...", "duration": 5}, ...]
            output_dir: 출력 디렉토리
            voice: 음성 설정 (기본: config에서)
        
        Returns:
            분할된 오디오 파일 경로 목록
        """
        voice = voice or TTS_VOICE_NAME
        
        # 0. 기존 오디오 파일 정리 (WAV만 사용, MP3 제거)
        import glob
        for pattern in ["audio_scene_*.wav", "audio_scene_*.mp3"]:
            for old_file in glob.glob(os.path.join(output_dir, pattern)):
                try:
                    os.unlink(old_file)
                except Exception:
                    pass
        
        # 1. 전체 텍스트 조합
        # 문장 사이에 명시적인 3초 휴식 태그를 추가하여 분할 정확도 테스트 (사용자 요청)
        # SSML 태그가 작동하려면 <speak> 태그로 감싸야 함
        texts = [scene['audio_text'].strip() for scene in scenes]
        inner_text = ' <break time="3s"/> \n'.join(texts)
        full_text = f"<speak>{inner_text}</speak>"
        
        print(f"\n   🎤 [통합 오디오 생성 시작]")
        print(f"   총 {len(scenes)}개 문장을 한 번에 생성합니다")
        print(f"   전체 텍스트 길이: {len(full_text)}자")
        print(f"   Voice: {voice}\n")
        
        # 2. 전체 오디오 생성
        temp_full_audio = os.path.join(output_dir, "_temp_full_audio.wav")
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                
                response = self.client.models.generate_content(
                    model=TTS_MODEL,
                    contents=full_text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice,
                                )
                            )
                        ),
                    )
                )
                
                if (response.candidates and 
                    response.candidates[0].content.parts and 
                    response.candidates[0].content.parts[0].inline_data):
                    
                    audio_data = response.candidates[0].content.parts[0].inline_data.data
                    self._save_wav_file(temp_full_audio, audio_data)
                    print(f"   ✅ 전체 오디오 생성 완료")
                    break
                else:
                    raise ValueError("No audio data in response")
                    
            except Exception as e:
                if attempt >= MAX_RETRIES:
                    raise Exception(f"TTS 생성 실패: {e}")
                continue
        
        # 3. Silence 기반 분할
        print(f"\n   ✂️  [오디오 분할 시작]")
        
        # 텍스트 길이와 예상 시간 정보 추출
        texts = [scene['audio_text'].strip() for scene in scenes]
        text_lengths = [len(t) for t in texts]
        expected_durations = [scene.get('duration', 0) for scene in scenes]
        
        audio_paths = self._split_audio_by_silence(
            temp_full_audio, 
            output_dir, 
            len(scenes),
            text_lengths=text_lengths,
            expected_durations=expected_durations
        )
        
        # 4. 임시 파일 삭제 (사용자 요청으로 보존)
        if os.path.exists(temp_full_audio):
            # os.unlink(temp_full_audio)
            print(f"   ℹ️  임시 오디오 파일 보존됨: {temp_full_audio}")
        
        # 5. 각 scene에 오디오 경로와 duration 할당
        for idx, (scene, audio_path) in enumerate(zip(scenes, audio_paths)):
            if audio_path and os.path.exists(audio_path):
                scene['audio_path'] = audio_path
                scene['duration'] = self.get_audio_duration(audio_path)
                print(f"      Scene {idx + 1}: {scene['duration']:.2f}초")
            else:
                raise Exception(f"Scene {idx + 1} 오디오 분할 실패")
        
        total_duration = sum(s['duration'] for s in scenes)
        print(f"\n   ✅ 분할 완료: {len(audio_paths)}개 파일")
        print(f"   📏 전체 길이: {total_duration:.2f}초\n")
        
        return audio_paths
    
    def _split_audio_by_silence(self, audio_path: str, output_dir: str, expected_chunks: int, text_lengths: list = None, expected_durations: list = None):
        """
        Silence 기반으로 오디오 분할. 실패 시 예상 시간(또는 텍스트 길이) 비율로 분할.
        
        Args:
            audio_path: 전체 오디오 파일 경로
            output_dir: 출력 디렉토리
            expected_chunks: 예상 분할 개수
            text_lengths: 각 청크에 해당하는 텍스트 길이 목록 (비율 계산용 Fallback 2순위)
            expected_durations: 각 청크에 해당하는 예상 시간 목록 (비율 계산용 Fallback 1순위)
        
        Returns:
            분할된 오디오 파일 경로 목록
        """
        from pydub import AudioSegment
        from pydub.silence import split_on_silence, detect_silence
        
        print(f"   예상 분할 개수: {expected_chunks}개")
        
        # 오디오 로드
        audio = AudioSegment.from_wav(audio_path)
        total_duration_ms = len(audio)
        print(f"   전체 오디오 길이: {total_duration_ms / 1000:.2f}초")
        
        # Silence 기반 분할 시도 (여러 threshold로)
        chunks = None
        
        # 단계적으로 silence threshold 조정
        from src.config.audio_config import SILENCE_CONFIGS
        silence_configs = SILENCE_CONFIGS
        
        for config in silence_configs:
            chunks = split_on_silence(
                audio,
                min_silence_len=config["min_silence_len"],
                silence_thresh=config["silence_thresh"],
                keep_silence=config["keep_silence"]
            )
            
            print(f"   시도: silence_len={config['min_silence_len']}ms, "
                  f"thresh={config['silence_thresh']}dB → {len(chunks)}개 분할")
            
            if len(chunks) == expected_chunks:
                break
            elif len(chunks) > expected_chunks:
                # 너무 많이 분할됨 → 인접 chunk 병합
                chunks = self._merge_chunks(chunks, expected_chunks)
                break
        
        # 분할 개수가 맞지 않으면 비율로 강제 분할 (Fallback)
        # 분할 개수가 맞지 않으면 비율로 강제 분할 (Fallback)
        if len(chunks) != expected_chunks:
            print(f"   ⚠️  Silence 분할 결과({len(chunks)}개)가 예상({expected_chunks}개)과 다름")
            
            # [수정] 대본 상의 Duration은 부정확하므로, 텍스트 길이(글자수)를 최우선 기준으로 삼음
            if text_lengths and len(text_lengths) == expected_chunks:
                print(f"   📐 텍스트 길이 비율로 분할합니다 (우선순위 높음)")
                chunks = self._split_proportional(audio, text_lengths)
            
            elif expected_durations and len(expected_durations) == expected_chunks:
                print(f"   📐 예상 시간(Duration) 비율로 분할합니다 (Fallback)")
                chunks = self._split_proportional(audio, expected_durations)
                
            else:
                print(f"   📐 균등 분할로 대체합니다 (정보 부족)")
                chunks = self._split_evenly(audio, expected_chunks)
        
        # 각 chunk 저장
        audio_paths = []
        for idx, chunk in enumerate(chunks):
            # 앞뒤에 짧은 silence 추가 (자연스러운 전환)
            silence_padding = AudioSegment.silent(duration=50)  # 50ms
            padded_chunk = silence_padding + chunk + silence_padding
            
            output_path = os.path.join(output_dir, f"audio_scene_{idx + 1}.wav")
            padded_chunk.export(output_path, format="wav")
            audio_paths.append(output_path)
        
        return audio_paths
    
    def _merge_chunks(self, chunks: list, target_count: int):
        """인접한 짧은 chunk들을 병합하여 target_count에 맞춤."""
        from pydub import AudioSegment
        
        while len(chunks) > target_count:
            # 가장 짧은 chunk 찾기
            min_idx = min(range(len(chunks)), key=lambda i: len(chunks[i]))
            
            # 인접 chunk와 병합 (앞쪽 우선, 없으면 뒤쪽)
            if min_idx > 0:
                chunks[min_idx - 1] = chunks[min_idx - 1] + chunks[min_idx]
                chunks.pop(min_idx)
            elif min_idx < len(chunks) - 1:
                chunks[min_idx] = chunks[min_idx] + chunks[min_idx + 1]
                chunks.pop(min_idx + 1)
            else:
                break
        
        return chunks
    
    def _split_proportional(self, audio, reference_values: list):
        """기준 값(텍스트 길이 or 예상 시간)에 비례하여 오디오를 분할."""
        total_value = sum(reference_values)
        if total_value == 0:
            return self._split_evenly(audio, len(reference_values))
            
        total_audio_ms = len(audio)
        chunks = []
        start_ms = 0
        
        for i, value in enumerate(reference_values):
            # 마지막 청크는 끝까지
            if i == len(reference_values) - 1:
                chunks.append(audio[start_ms:])
            else:
                # 비율 계산
                ratio = value / total_value
                duration_ms = int(total_audio_ms * ratio)
                end_ms = start_ms + duration_ms
                
                # 단순히 시간비례로 자르면 문장 중간이 잘릴 수 있음
                # (TODO: 향후 근처 Silence 탐색 로직 추가 가능)
                chunks.append(audio[start_ms:end_ms])
                start_ms = end_ms
                
        return chunks

    def _split_evenly(self, audio, count: int):
        """오디오를 균등하게 분할."""
        from pydub import AudioSegment
        
        total_len = len(audio)
        chunk_len = total_len // count
        
        chunks = []
        for i in range(count):
            start = i * chunk_len
            end = start + chunk_len if i < count - 1 else total_len
            chunks.append(audio[start:end])
        
        return chunks


if __name__ == "__main__":
    audio = AudioGenerator()
    # audio.generate_speech("안녕하세요, 구글 gTTS 테스트입니다.", "test_gtts.mp3")
