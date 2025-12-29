"""
오디오 설정 파일 (Audio Configuration)

TTS 음성, 침묵 감지, 오디오 싱크 관련 설정을 관리합니다.
"""

# ============================================
# TTS 설정
# ============================================
TTS_VOICE_NAME = "Kore"  # Kore (여성), Aoede (여성), Charon (남성), Fenrir (남성), Puck (남성)

# ============================================
# 침묵 감지 (Silence Detection) 설정
# ============================================
# 오디오 분할 시 시도할 단계별 설정 (엄격한 기준 -> 느슨한 기준)
SILENCE_CONFIGS = [
    {"min_silence_len": 400, "silence_thresh": -35, "keep_silence": 150},
    {"min_silence_len": 300, "silence_thresh": -40, "keep_silence": 100},
    {"min_silence_len": 250, "silence_thresh": -45, "keep_silence": 80},
    {"min_silence_len": 200, "silence_thresh": -50, "keep_silence": 50},
]

# 앞뒤 패딩 (자연스러운 전환을 위해 추가할 무음 길이)
AUDIO_PADDING_MS = 50
