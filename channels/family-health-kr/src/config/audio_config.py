# TTS 음성 설정
TTS_VOICE_NAME = "Kore"  # Gemini TTS 음성

# 오디오 분할을 위한 Silence 설정 (단계별 시도)
# min_silence_len: 무음으로 판단할 최소 길이 (ms)
# silence_thresh: 무음 판단 데시벨 임계값 (dV)
# keep_silence: 분할 후 남길 무음 길이 (ms)
SILENCE_CONFIGS = [
    # 0단계: 아주 긴 무음 (long pause 대응)
    {"min_silence_len": 800, "silence_thresh": -30, "keep_silence": 250},
    # 1단계: 길고 명확한 무음 기준
    {"min_silence_len": 700, "silence_thresh": -30, "keep_silence": 200},
    # 2단계: 중간-긴 무음
    {"min_silence_len": 600, "silence_thresh": -28, "keep_silence": 175},
    # 3단계: 중간 길이 무음
    {"min_silence_len": 500, "silence_thresh": -25, "keep_silence": 150},
    # 4단계: 짧은 무음 (민감하게)
    {"min_silence_len": 400, "silence_thresh": -20, "keep_silence": 100},
]
