# TTS Voice Settings for Money Bite (English)
TTS_VOICE_NAME = "Kore"  # Gemini TTS voice — change to English voice when available

# NOTE: For English narration, consider these Gemini TTS voices:
# - "Aoede" (Female, warm)
# - "Charon" (Male, deep)  
# - "Fenrir" (Male, energetic)
# - "Kore" (Female, clear)
# - "Puck" (Male, friendly)
# Check available voices with: python3 list_models.py

# Silence splitting settings for audio segmentation (step-by-step attempts)
# min_silence_len: Minimum silence length to detect (ms)
# silence_thresh: Silence threshold in dB
# keep_silence: Silence to keep after splitting (ms)
SILENCE_CONFIGS = [
    # 1000ms silence with various thresholds (lenient → strict)
    {"min_silence_len": 1000, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 1000, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 1000, "silence_thresh": -25, "keep_silence": 300},
    # 900ms silence
    {"min_silence_len": 900, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 900, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 900, "silence_thresh": -25, "keep_silence": 300},
    # 800ms silence
    {"min_silence_len": 800, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 800, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 800, "silence_thresh": -25, "keep_silence": 300},
    # 700ms silence
    {"min_silence_len": 700, "silence_thresh": -30, "keep_silence": 300},
    {"min_silence_len": 700, "silence_thresh": -28, "keep_silence": 300},
    {"min_silence_len": 700, "silence_thresh": -25, "keep_silence": 300},
]
