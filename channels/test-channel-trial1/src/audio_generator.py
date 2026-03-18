import os
import logging
import wave
import tempfile
import time
from gtts import gTTS
from google import genai
from google.genai import types
from config.model_config import TTS_MODEL, MAX_RETRIES, RETRY_DELAY
try:
    from config.model_config import TTS_FALLBACK_MODEL
except ImportError:
    TTS_FALLBACK_MODEL = None
from config.audio_config import TTS_VOICE_NAME

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
        self.use_tts_fallback_mode = False  # 메인 TTS 실패 시 이후 Fallback으로 전환
        self.tts_fallback_count = 0  # Fallback 사용 횟수

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

    def generate_speech_unified(self, scenes: list, output_dir: str, voice: str = None, tts_fallback: bool = False, tts_style: str = "", test_mode: bool = False):
        """
        [Unified 모드] 전체 대본을 한 번에 TTS 생성 후 silence 기반으로 분할.
        일관된 톤과 자연스러운 억양을 유지합니다.
        
        Args:
            scenes: 장면 목록 [{"scene_id": 1, "audio_text": "...", "duration": 5}, ...]
            output_dir: 출력 디렉토리
            voice: 음성 설정 (기본: config에서)
            tts_fallback: Fallback 허용 여부 (True: gTTS 사용, False: 실패 시 종료)
        
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
        # [수정] 사용자가 구체적으로 요청한 [medium pause][medium pause] (표준 일시중지 2회) 적용
        # 문장 구분에 가장 효과적임 (Silence 감지 용이)
        texts = [scene['audio_text'].strip() for scene in scenes]
        full_text = ' [medium pause] [medium pause] '.join(texts)
        
        # Director's Notes Pacing 적용
        if tts_style:
            full_text = f"### DIRECTOR'S NOTES\nPacing: {tts_style}\n#### TRANSCRIPT\n{full_text}"
            print(f"   🎭 TTS Style: {tts_style}")
        
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
                    print(f"   ⚠️  Gemini TTS 실패: {e}")
                    
                    # Fallback TTS 모델 시도
                    if TTS_FALLBACK_MODEL:
                        print(f"   🔄 Fallback TTS 모델({TTS_FALLBACK_MODEL})로 시도합니다.")
                        try:
                            response = self.client.models.generate_content(
                                model=TTS_FALLBACK_MODEL,
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
                                self.tts_fallback_count += 1
                                print(f"   ✅ Fallback TTS 모델로 전체 오디오 생성 완료")
                                break
                            else:
                                raise ValueError("No audio data in fallback response")
                        except Exception as fallback_e:
                            print(f"   ⚠️  Fallback TTS도 실패: {fallback_e}")
                    
                    # gTTS fallback (기존 로직 유지)
                    if tts_fallback:
                        print(f"   🔄 gTTS (Google Translate TTS)로 대체합니다.")
                        try:
                            tts = gTTS(text=full_text, lang='ja')
                            tts.save(temp_full_audio)
                            print(f"   ✅ gTTS 전체 오디오 생성 완료")
                            break
                        except Exception as gtts_e:
                            raise Exception(f"모든 TTS 생성 실패 (Gemini: {e}, Fallback: TTS_FALLBACK_MODEL, gTTS: {gtts_e})")
                    else:
                        raise Exception(f"Gemini TTS 실패 (재시도 {MAX_RETRIES}회 초과): {e}")
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

    def generate_speech_individual(self, scenes: list, output_dir: str, voice: str = None, tts_style: str = ""):
        """
        [Individual 모드] 각 Scene별로 개별 TTS 생성.
        문장마다 독립적으로 API를 호출하여 오디오 파일을 직접 생성합니다.
        
        Args:
            scenes: 장면 목록 [{"scene_id": 1, "audio_text": "...", "duration": 5}, ...]
            output_dir: 출력 디렉토리
            voice: 음성 설정 (기본: config에서)
        
        Returns:
            생성된 오디오 파일 경로 목록
        """
        voice = voice or TTS_VOICE_NAME
        
        # 0. 기존 오디오 파일 정리
        import glob
        for pattern in ["audio_scene_*.wav", "audio_scene_*.mp3"]:
            for old_file in glob.glob(os.path.join(output_dir, pattern)):
                try:
                    os.unlink(old_file)
                except Exception:
                    pass
        
        print(f"\n   🎤 [Individual 모드 - 개별 오디오 생성 시작]")
        print(f"   총 {len(scenes)}개 문장을 각각 생성합니다")
        print(f"   Voice: {voice}\n")
        
        audio_paths = []
        
        for idx, scene in enumerate(scenes):
            scene_text = scene['audio_text'].strip()
            output_path = os.path.join(output_dir, f"audio_scene_{idx + 1}.wav")
            
            # Director's Notes Pacing 적용
            tts_input = scene_text
            if tts_style:
                tts_input = f"### DIRECTOR'S NOTES\nPacing: {tts_style}\n#### TRANSCRIPT\n{scene_text}"
            
            print(f"   🎤 Scene {idx + 1}/{len(scenes)}: {scene_text[:60]}{'...' if len(scene_text) > 60 else ''}")
            
            # Fallback 모드가 활성화된 경우 바로 Fallback 모델 사용
            current_tts_model = TTS_MODEL
            if self.use_tts_fallback_mode and TTS_FALLBACK_MODEL:
                current_tts_model = TTS_FALLBACK_MODEL
                print(f"      🔄 Fallback 모델 사용: {TTS_FALLBACK_MODEL}")
            
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    if attempt > 1:
                        print(f"      🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                    
                    response = self.client.models.generate_content(
                        model=current_tts_model,
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
                    
                    if (response.candidates and 
                        response.candidates[0].content.parts and 
                        response.candidates[0].content.parts[0].inline_data):
                        
                        audio_data = response.candidates[0].content.parts[0].inline_data.data
                        self._save_wav_file(output_path, audio_data)
                        
                        scene['audio_path'] = output_path
                        scene['duration'] = self.get_audio_duration(output_path)
                        audio_paths.append(output_path)
                        
                        if self.use_tts_fallback_mode:
                            self.tts_fallback_count += 1
                        print(f"      ✅ 완료 ({scene['duration']:.2f}초)")
                        break
                    else:
                        raise ValueError("No audio data in response")
                        
                except Exception as e:
                    if attempt >= MAX_RETRIES:
                        error_str = str(e)
                        logger.error(f"Scene {idx + 1} TTS failed after {MAX_RETRIES} attempts: {e}")
                        
                        # Fallback 모드가 아니고 Fallback 모델이 있으면 시도
                        if not self.use_tts_fallback_mode and TTS_FALLBACK_MODEL:
                            print(f"      ⚠️  메인 TTS 실패, Fallback 모델({TTS_FALLBACK_MODEL}) 시도 중...")
                            print(f"      🔄 이후 장면들도 Fallback 모델로 전환합니다.")
                            try:
                                response = self.client.models.generate_content(
                                    model=TTS_FALLBACK_MODEL,
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
                                
                                if (response.candidates and 
                                    response.candidates[0].content.parts and 
                                    response.candidates[0].content.parts[0].inline_data):
                                    
                                    audio_data = response.candidates[0].content.parts[0].inline_data.data
                                    self._save_wav_file(output_path, audio_data)
                                    
                                    scene['audio_path'] = output_path
                                    scene['duration'] = self.get_audio_duration(output_path)
                                    audio_paths.append(output_path)
                                    
                                    self.use_tts_fallback_mode = True  # 이후 장면은 Fallback
                                    self.tts_fallback_count += 1
                                    print(f"      ✅ Fallback 모델로 성공! ({scene['duration']:.2f}초)")
                                    break
                                else:
                                    raise ValueError("No audio data in fallback response")
                            except Exception as fallback_e:
                                logger.error(f"Fallback TTS also failed for scene {idx + 1}: {fallback_e}")
                                print(f"      ❌ Scene {idx + 1} 생성 실패 (Primary + Fallback): {error_str}")
                                raise Exception(f"Scene {idx + 1} TTS 실패 (Primary: {error_str}, Fallback: {fallback_e})")
                        else:
                            print(f"      ❌ Scene {idx + 1} 생성 실패: {error_str}")
                            raise Exception(f"Scene {idx + 1} TTS 실패 (재시도 {MAX_RETRIES}회 초과): {error_str}")
                    continue
        
        total_duration = sum(s['duration'] for s in scenes)
        print(f"\n   ✅ 개별 생성 완료: {len(audio_paths)}개 파일")
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
        from config.audio_config import SILENCE_CONFIGS
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
                print(f"   ✅ 성공! silence_len={config['min_silence_len']}ms, thresh={config['silence_thresh']}dB 사용")
                break
            elif len(chunks) > expected_chunks:
                # 너무 많이 분할됨 → 인접 chunk 병합
                chunks = self._merge_chunks(chunks, expected_chunks)
                print(f"   ✅ 병합 후 성공! silence_len={config['min_silence_len']}ms (병합: {len(chunks)}개)")
                break
        
        # 분할 개수가 맞지 않으면 오류 발생 및 종료
        if len(chunks) != expected_chunks:
            error_msg = f"❌ 오디오 분할 실패! 예상: {expected_chunks}개, 결과: {len(chunks)}개"
            print(f"\n   {error_msg}")
            print(f"   💡 원인: TTS 음성에서 충분한 무음 구간이 감지되지 않았습니다.")
            print(f"   💡 해결책: 프롬프트에서 [medium pause] 개수를 늘리거나, SILENCE_CONFIGS를 조정하세요.")
            raise Exception(error_msg)
        
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


    def _generate_with_gtts(self, scenes: list, output_dir: str):
        """🧪 Test Mode: gTTS로 개별 오디오 파일을 API 호출 없이 즉시 생성."""
        import glob
        import tempfile
        from pydub import AudioSegment
        
        print(f"\n   🧪 [테스트 모드] Gemini TTS 대신 gTTS로 오디오 생성")
        
        for pattern in ["audio_scene_*.wav", "audio_scene_*.mp3"]:
            for old_file in glob.glob(os.path.join(output_dir, pattern)):
                try:
                    os.unlink(old_file)
                except Exception:
                    pass
        
        audio_paths = []
        for idx, scene in enumerate(scenes):
            scene_text = scene['audio_text'].strip()
            output_path = os.path.join(output_dir, f"audio_scene_{idx + 1}.wav")
            
            lang = 'en'
            for ch in scene_text[:20]:
                if '\u3040' <= ch <= '\u30FF' or '\u4E00' <= ch <= '\u9FFF':
                    lang = 'ja'
                    break
                elif '\uAC00' <= ch <= '\uD7AF':
                    lang = 'ko'
                    break
            
            try:
                temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_mp3_path = temp_mp3.name
                temp_mp3.close()
                
                tts = gTTS(text=scene_text, lang=lang)
                tts.save(temp_mp3_path)
                
                audio_seg = AudioSegment.from_mp3(temp_mp3_path)
                audio_seg.export(output_path, format='wav')
                os.unlink(temp_mp3_path)
                
                scene['audio_path'] = output_path
                scene['duration'] = self.get_audio_duration(output_path)
                audio_paths.append(output_path)
                print(f"      ✅ Scene {idx + 1}: gTTS 생성 ({scene['duration']:.2f}초)")
            except Exception as e:
                print(f"      ❌ Scene {idx + 1}: gTTS 실패 - {e}")
                raise
        
        total_duration = sum(s['duration'] for s in scenes)
        print(f"\n   ✅ 테스트 오디오 생성 완료: {len(audio_paths)}개 파일")
        print(f"   📏 전체 길이: {total_duration:.2f}초\n")
        return audio_paths


if __name__ == "__main__":
    audio = AudioGenerator()
    # audio.generate_speech("안녕하세요, 구글 gTTS 테스트입니다.", "test_gtts.mp3")
