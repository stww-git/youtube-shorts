"""
YouTube Shorts 자동 생성 시스템

채널별로 독립적인 파이프라인을 실행합니다.
"""

import argparse
import warnings
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.channel_manager import (
    get_channel_config, validate_channel, 
    get_channel_module, get_output_dir
)
from core.utils import print_header, check_environment

# Suppress warnings
warnings.filterwarnings('ignore')
import logging
logging.captureWarnings(True)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

try:
    import urllib3
    urllib3.disable_warnings()
except:
    pass

# Load environment variables
load_dotenv()

# ==============================================================================
# 🎮 사용자 설정 (USER CONFIGURATION)
# ==============================================================================

# 1. 실행할 채널 선택 (Active Channel)
#    - 아래 CHANNELS 딕셔너리에 있는 채널 중 하나를 선택하세요.
ACTIVE_CHANNEL = "test-channel-trial1"

# 2. 채널별 설정 (Per-Channel Settings)
#    - 각 채널의 테스트 모드, 업로드 여부를 개별 설정합니다.
#    - 새 채널 추가 시 add_channel.py가 자동으로 여기에 추가합니다.
CHANNELS = {
    "sokpyeonhan": {
        "api_key_env": "GOOGLE_API_KEY",  # 사용할 API 키 환경변수명 (GitHub Secrets)
        "enabled": True,         # True: GitHub Actions 스케줄 실행
        "test_mode": False,        # False: 실제 이미지 생성
        "upload": True,          # True: YouTube 업로드
        "privacy": "public",      # public / unlisted / private
        "subtitle_mode": "phrase", # static / accumulate / single / stack / phrase (모드별 상세 설정: subtitle/config.py)
        "ai_subtitle_effects": True,  # True: AI가 어절별 효과 판단 / False: 기존 방식
        "ken_burns_effect": True,      # True: 이미지 천천히 줌 인 효과 / False: 정지 이미지
        "ken_burns_zoom": 0.08,        # 줌 인 강도 (0.03=약하게, 0.05=보통, 0.10=강하게)
        "tts_mode": "individual",  # unified: 통합 생성 후 무음 분할 / individual: 문장별 개별 생성
        "tts_style": "Speak at a slightly faster",  # TTS 속도/스타일 지시 (빈 문자열: 기본 속도) / unified 모드에서도 적용됨
        "tts_voice_name": "Kore",  # Gemini TTS 음성 (Kore, Aoede, Charon, Fenrir, Puck 등)

        "summary_card_show_title": False,  # True: 핵심카드에도 제목 표시 / False: 핵심카드에서 제목 숨김
        "summary_card": True,    # True: 영상 끝에 핵심 정보 카드 추가
        "show_title": True,      # True: 전체 영상 상단에 제목 + 검은 배경 표시 / False: 제목 숨김
        "summary_in_description": True,  # True: 핵심 정보를 YouTube 설명에 포함
        "summary_card_duration": 2.0,  # 핵심 정보 카드 노출 시간 (초)
        "parallel": False,        # True: 이미지 병렬 생성
        "tts_fallback": False,  # True: TTS 실패 시 gTTS로 대체 / False: 바로 종료
        "disclaimer": False,      # True: 면책 조항 추가
        "bgm_enabled": False,     # True: 배경음악 사용
        "bgm_volume": 0.1,       # 배경음악 볼륨 (0.0 ~ 1.0, 나레이션 대비 비율)
        "bgm_file": "cooking.mp3", # assets/bgm/ 폴더 내 파일명
    },

    "money-bite": {
        "api_key_env": "GOOGLE_API_KEY_2",  # 사용할 API 키 환경변수명
        "enabled": True,         # True: GitHub Actions 스케줄 실행
        "test_mode": False,        # False: 실제 이미지 생성
        "upload": True,          # True: YouTube 업로드
        "privacy": "public",      # public / unlisted / private
        "subtitle_mode": "phrase", # static / accumulate / single / stack / phrase (모드별 상세 설정: subtitle/config.py)
        "ai_subtitle_effects": True,  # True: AI가 어절별 효과 판단 / False: 기존 방식
        "ken_burns_effect": True,     # True: 이미지 천천히 줌 인 효과 / False: 정지 이미지
        "ken_burns_zoom": 0.08,        # 줌 인 강도 (0.03=약하게, 0.05=보통, 0.10=강하게)
        "tts_voice_name": "Kore",  # Gemini TTS 음성 (Kore, Aoede, Charon, Fenrir, Puck 등)
        "tts_mode": "individual",  # unified: 통합 생성 후 무음 분할 / individual: 문장별 개별 생성
        "tts_style": "Speak at a slightly faster, energetic pace",  # TTS 속도/스타일 지시 (빈 문자열: 기본 속도) / unified 모드에서도 적용됨
        "summary_card_show_title": False,  # True: 핵심카드에도 제목 표시 / False: 핵심카드에서 제목 숨김

        "summary_card": True,    # True: 영상 끝에 핵심 정보 카드 추가
        "show_title": True,      # True: 전체 영상 상단에 제목 + 검은 배경 표시 / False: 제목 숨김
        "summary_in_description": True,  # True: 핵심 정보를 YouTube 설명에 포함
        "summary_card_duration": 2.0,  # 핵심 정보 카드 노출 시간 (초)
        "parallel": False,        # True: 이미지 병렬 생성
        "tts_fallback": False,  # True: TTS 실패 시 gTTS로 대체 / False: 바로 종료
        "disclaimer": False,      # True: 면책 조항 추가
        "bgm_enabled": False,     # True: 배경음악 사용
        "bgm_volume": 0.1,       # 배경음악 볼륨 (0.0 ~ 1.0, 나레이션 대비 비율)
        "bgm_file": "cooking.mp3", # assets/bgm/ 폴더 내 파일명
    },

    "money-bite-us": {
        "api_key_env": "GOOGLE_API_KEY_3",  # 사용할 API 키 환경변수명
        "enabled": True,         # True: GitHub Actions 스케줄 실행
        "test_mode": False,        # False: 실제 이미지 생성
        "upload": True,          # True: YouTube 업로드
        "privacy": "public",      # public / unlisted / private
        "subtitle_mode": "phrase", # static / accumulate / single / stack / phrase (모드별 상세 설정: subtitle/config.py)
        "ai_subtitle_effects": True,  # True: AI가 어절별 효과 판단 / False: 기존 방식
        "ken_burns_effect": True,     # True: 이미지 천천히 줌 인 효과 / False: 정지 이미지
        "ken_burns_zoom": 0.08,        # 줌 인 강도 (0.03=약하게, 0.05=보통, 0.10=강하게)
        "tts_voice_name": "Kore",  # Gemini TTS 음성 (Kore, Aoede, Charon, Fenrir, Puck 등)
        "tts_mode": "individual",  # unified: 통합 생성 후 무음 분할 / individual: 문장별 개별 생성
        "tts_style": "Speak at a slightly faster, energetic pace",  # TTS 속도/스타일 지시 (빈 문자열: 기본 속도) / unified 모드에서도 적용됨
        "summary_card_show_title": False,  # True: 핵심카드에도 제목 표시 / False: 핵심카드에서 제목 숨김

        "summary_card": True,    # True: 영상 끝에 핵심 정보 카드 추가
        "show_title": True,      # True: 전체 영상 상단에 제목 + 검은 배경 표시 / False: 제목 숨김
        "summary_in_description": True,  # True: 핵심 정보를 YouTube 설명에 포함
        "summary_card_duration": 2.0,  # 핵심 정보 카드 노출 시간 (초)
        "parallel": False,        # True: 이미지 병렬 생성
        "tts_fallback": False,  # True: TTS 실패 시 gTTS로 대체 / False: 바로 종료
        "disclaimer": False,      # True: 면책 조항 추가
        "bgm_enabled": False,     # True: 배경음악 사용
        "bgm_volume": 0.1,       # 배경음악 볼륨 (0.0 ~ 1.0, 나레이션 대비 비율)
        "bgm_file": "cooking.mp3", # assets/bgm/ 폴더 내 파일명
    },

    "money-bite-jp": {
        "api_key_env": "GOOGLE_API_KEY_3",  # 사용할 API 키 환경변수명
        "enabled": True,         # True: GitHub Actions 스케줄 실행
        "test_mode": False,        # False: 실제 이미지 생성
        "upload": True,          # True: YouTube 업로드
        "privacy": "public",      # public / unlisted / private
        "subtitle_mode": "phrase", # static / accumulate / single / stack / phrase (모드별 상세 설정: subtitle/config.py)
        "ai_subtitle_effects": True,  # True: AI가 어절별 효과 판단 / False: 기존 방식
        "ken_burns_effect": True,     # True: 이미지 천천히 줌 인 효과 / False: 정지 이미지
        "ken_burns_zoom": 0.08,        # 줌 인 강도 (0.03=약하게, 0.05=보통, 0.10=강하게)
        "tts_voice_name": "Aoede",  # Gemini TTS 음성 (Aoede가 일본어 자연스러움)
        "tts_mode": "individual",  # unified / individual
        "tts_style": "Speak naturally and energetically in Japanese",  # 일본어 자연스러운 톤
        "summary_card_show_title": False,  # True: 핵심카드에도 제목 표시 / False: 핵심카드에서 제목 숨김

        "summary_card": True,    # True: 영상 끝에 핵심 정보 카드 추가
        "show_title": True,      # True: 전체 영상 상단에 제목 + 검은 배경 표시 / False: 제목 숨김
        "summary_in_description": True,  # True: 핵심 정보를 YouTube 설명에 포함
        "summary_card_duration": 2.0,  # 핵심 정보 카드 노출 시간 (초)
        "parallel": False,        # True: 이미지 병렬 생성
        "tts_fallback": False,  # True: TTS 실패 시 gTTS로 대체 / False: 바로 종료
        "disclaimer": False,      # True: 면책 조항 추가
        "bgm_enabled": False,     # True: 배경음악 사용
        "bgm_volume": 0.1,       # 배경음악 볼륨 (0.0 ~ 1.0, 나레이션 대비 비율)
        "bgm_file": "cooking.mp3", # assets/bgm/ 폴더 내 파일명
    },

    "test-channel-trial1": {
        "api_key_env": "GOOGLE_API_KEY",  # 사용할 API 키 환경변수명
        "enabled": False,          # True: 스케줄 실행
        "test_mode": False,        # True: 테스트 모드
        "upload": False,          # True: 업로드
        "privacy": "private",     # public / unlisted / private
        "parallel": False,
        "tts_fallback": False,  # False: 실패 시 바로 종료
        "summary_card": False,    # True: 영상 끝에 핵심 정보 카드 추가
        "summary_card_duration": 2.0,  # 핵심 정보 카드 노출 시간 (초)
        "summary_in_description": True,  # True: 핵심 정보를 YouTube 설명에 포함
        "disclaimer": False,      # True: 면책 조항 추가
        "bgm_enabled": False,     # True: 배경음악 사용
        "bgm_volume": 0.05,       # 배경음악 볼륨 (0.0 ~ 1.0, 나레이션 대비 비율)
        "bgm_file": "cooking.mp3", # assets/bgm/ 폴더 내 파일명
        "subtitle_mode": "static",  # static: 통짜 표시 / accumulate: 어절 누적 / single: 한 어절씩
        "typing_speed": 0.20,
        "tts_voice_name": "Kore",
    },
    "family-health-kr": {
        "api_key_env": "GOOGLE_API_KEY",  # 사용할 API 키 환경변수명
        "enabled": False,          # True: 스케줄 실행
        "test_mode": True,        # True: 테스트 모드 (이미지 생성 생략)
        "upload": True,          # True: YouTube 업로드
        "privacy": "private",     # public / unlisted / private
        "parallel": False,        # True: 이미지 병렬 생성
        "tts_fallback": False,  # False: 실패 시 바로 종료
        "summary_card": True,     # True: 영상 끝에 핵심 정보 카드 추가
        "summary_card_duration": 2.0,  # 핵심 정보 카드 노출 시간 (초)
        "summary_in_description": False,  # True: 핵심 정보를 YouTube 설명에 포함
        "disclaimer": False,       # True: 영상 끝에 면책 조항 추가
        "bgm_enabled": False,      # True: 배경음악 사용
        "bgm_volume": 0.05,        # 배경음악 볼륨 (0.0 ~ 1.0, 나레이션 대비 비율)
        "bgm_file": "cooking.mp3",  # assets/bgm/ 폴더 내 파일명
        "subtitle_mode": "static",  # static: 통짜 표시 / accumulate: 어절 누적 / single: 한 어절씩
        "typing_speed": 0.5,
        "tts_voice_name": "Kore",
    },

    # 새 채널 추가 시 아래 형식으로 추가됩니다:
    # "channel-id": {
    #     "enabled": True,
    #     "test_mode": True,
    #     "upload": False,
    #     "privacy": "private",
    #     "parallel": False,
    #     "tts_fallback": False,
    # },
}

# ==============================================================================





def main():
    print_header("🎬 YouTube Shorts 자동 생성 시스템")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='YouTube Shorts Generator')
    parser.add_argument('--test', action='store_true', help='Test mode')
    parser.add_argument('--upload', action='store_true', help='Upload to YouTube')
    parser.add_argument('--channel', type=str, default=None, help='Target channel ID')
    args = parser.parse_args()
    
    # 채널 결정 (CLI 인자 > ACTIVE_CHANNEL)
    channel_id = args.channel if args.channel else ACTIVE_CHANNEL
    
    # 채널별 설정 가져오기
    if channel_id not in CHANNELS:
        print(f"   ❌ 채널 '{channel_id}'가 CHANNELS 설정에 없습니다.")
        print(f"   💡 main.py의 CHANNELS 딕셔너리에 채널을 추가하세요.")
        return
    
    channel_settings = CHANNELS[channel_id]
    
    # CLI 인자가 있으면 우선, 없으면 채널 설정 사용
    is_test_mode = args.test if args.test else channel_settings.get("test_mode", True)
    should_upload = args.upload if args.upload else channel_settings.get("upload", False)
    is_parallel = channel_settings.get("parallel", False)
    tts_fallback = channel_settings.get("tts_fallback", False)
    privacy_status = channel_settings.get("privacy", "private")  # main.py의 privacy 설정 사용
    include_summary_card = channel_settings.get("summary_card", False)  # 핵심 정보 카드 추가 여부
    summary_card_duration = channel_settings.get("summary_card_duration", 3.0)  # 카드 노출 시간
    summary_in_description = channel_settings.get("summary_in_description", False)  # 설명에 핵심 정보 포함
    include_disclaimer = channel_settings.get("disclaimer", False)  # 면책 조항 추가 여부
    bgm_enabled = channel_settings.get("bgm_enabled", False)  # 배경음악 사용 여부
    bgm_volume = channel_settings.get("bgm_volume", 0.1)  # 배경음악 볼륨
    bgm_file = channel_settings.get("bgm_file", None)  # 배경음악 파일명
    subtitle_mode = channel_settings.get("subtitle_mode", "static")  # 자막 모드 (static/accumulate/single/stack)
    typing_speed = channel_settings.get("typing_speed", 0.20)  # 타이핑 속도
    single_font_size = channel_settings.get("single_font_size", 100)  # single 모드 폰트 크기
    static_font_size = channel_settings.get("static_font_size", 80)  # static 모드 폰트 크기
    ai_subtitle_effects = channel_settings.get("ai_subtitle_effects", False)  # AI 자막 효과
    ken_burns_effect = channel_settings.get("ken_burns_effect", True)  # Ken Burns 줌 인 효과
    ken_burns_zoom = channel_settings.get("ken_burns_zoom", 0.05)  # 줌 인 강도
    tts_voice_name = channel_settings.get("tts_voice_name", "Kore")  # TTS 음성
    show_title = channel_settings.get("show_title", True)  # 영상 제목 표시 여부
    summary_card_show_title = channel_settings.get("summary_card_show_title", True)  # 핵심카드에 제목 표시 여부
    tts_mode = channel_settings.get("tts_mode", "unified")  # TTS 모드 (unified/individual)
    tts_style = channel_settings.get("tts_style", "")  # TTS 속도/스타일 지시 (Director's Notes Pacing)
    
    if not channel_id:
        print("   ❌ 채널이 선택되지 않았습니다.")
        return
    
    # 채널 정보 표시
    config = get_channel_config(channel_id)
    if config:
        print(f"\n   📺 타겟 채널: {config.get('display_name', channel_id)}")
        
        is_valid, message = validate_channel(channel_id)
        if not is_valid and should_upload:
            print(f"   ⚠️  {message}")
    else:
        print(f"\n   ❌ 채널 '{channel_id}' 설정을 찾을 수 없습니다.")
        return
    
    # 모드 표시
    if is_test_mode:
        print("\n   🧪 [TEST MODE] 이미지 생성을 건너뜁니다.\n")
    
    if should_upload:
        print("   🚀 [UPLOAD] 영상 생성 후 YouTube 업로드\n")
    else:
        print("   📁 [LOCAL] 영상 생성만 진행\n")
    
    check_environment()
    
    # 채널별 API 키 설정
    api_key_env = channel_settings.get("api_key_env", "GOOGLE_API_KEY")
    api_key = os.getenv(api_key_env)
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        print(f"   🔑 API 키: {api_key_env} 사용")
    else:
        print(f"   ⚠️  {api_key_env} 환경변수가 설정되지 않았습니다.")
    
    # 채널별 Pipeline 로드 및 실행
    try:
        pipeline_module = get_channel_module(channel_id, 'pipeline')
        
        # Pipeline 클래스가 있으면 사용, 없으면 함수 방식
        if hasattr(pipeline_module, 'RecipeVideoPipeline'):
            pipeline = pipeline_module.RecipeVideoPipeline()
            pipeline.run(
                test_mode=is_test_mode,
                image_parallel=is_parallel,
                upload_to_youtube=should_upload,
                channel_id=channel_id,
                tts_fallback=tts_fallback,
                privacy_status=privacy_status,
                include_summary_card=include_summary_card,
                summary_card_duration=summary_card_duration,
                summary_in_description=summary_in_description,
                include_disclaimer=include_disclaimer,
                bgm_enabled=bgm_enabled,
                bgm_volume=bgm_volume,
                bgm_file=bgm_file,
                subtitle_mode=subtitle_mode,
                typing_speed=typing_speed,
                single_font_size=single_font_size,
                static_font_size=static_font_size,
                ai_subtitle_effects=ai_subtitle_effects,
                tts_voice_name=tts_voice_name,
                ken_burns_effect=ken_burns_effect,
                ken_burns_zoom=ken_burns_zoom,
                show_title=show_title,
                summary_card_show_title=summary_card_show_title,
                tts_mode=tts_mode,
                tts_style=tts_style
            )
        elif hasattr(pipeline_module, 'run'):
            pipeline_module.run(
                test_mode=is_test_mode,
                image_parallel=is_parallel,
                upload_to_youtube=should_upload,
                channel_id=channel_id,
                tts_fallback=tts_fallback
            )
        else:
            print(f"   ❌ 채널 '{channel_id}'의 pipeline에 실행 가능한 함수가 없습니다.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"   ❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ 파이프라인 실행 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
