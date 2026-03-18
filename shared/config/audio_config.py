# TTS 음성 설정
TTS_VOICE_NAME = "Kore"  # Gemini TTS 음성

# 오디오 분할을 위한 Silence 설정 (단계별 시도)
# min_silence_len: 무음으로 판단할 최소 길이 (ms)
# silence_thresh: 무음 판단 데시벨 임계값 (dB)
# keep_silence: 분할 후 남길 무음 길이 (ms)
SILENCE_CONFIGS = [
    # 1000ms 무음에서 여러 thresh 시도 (관대 → 엄격)
    {"min_silence_len": 1000, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 1000, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 1000, "silence_thresh": -25, "keep_silence": 300},
    # 900ms 무음에서 여러 thresh 시도
    {"min_silence_len": 900, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 900, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 900, "silence_thresh": -25, "keep_silence": 300},
    # 800ms 무음에서 여러 thresh 시도
    {"min_silence_len": 800, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 800, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 800, "silence_thresh": -25, "keep_silence": 300},
    # 700ms 무음에서 여러 thresh 시도
    {"min_silence_len": 700, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 700, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 700, "silence_thresh": -25, "keep_silence": 300},
]
