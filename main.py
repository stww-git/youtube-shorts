"""
YouTube Shorts 자동 생성 시스템

채널별로 독립적인 파이프라인을 실행합니다.
"""

import argparse
import warnings
import sys
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
ACTIVE_CHANNEL = "sokpyeonhan"

# 2. 채널별 설정 (Per-Channel Settings)
#    - 각 채널의 테스트 모드, 업로드 여부를 개별 설정합니다.
#    - 새 채널 추가 시 add_channel.py가 자동으로 여기에 추가합니다.
CHANNELS = {
    "sokpyeonhan": {
        "enabled": True,         # True: GitHub Actions 스케줄 실행
        "test_mode": False,        # False: 실제 이미지 생성
        "upload": True,          # True: YouTube 업로드
        "privacy": "public",      # public / unlisted / private
        "parallel": False,        # True: 이미지 병렬 생성
        "allow_fallback": False,  # True: TTS 실패 시 gTTS로 대체 / False: 바로 종료
    },
    "test-channel-trial1": {
        "enabled": False,          # True: 스케줄 실행
        "test_mode": True,        # True: 테스트 모드
        "upload": False,          # True: 업로드
        "privacy": "private",     # public / unlisted / private
        "parallel": False,
        "allow_fallback": False,  # False: 실패 시 바로 종료
    },
    # 새 채널 추가 시 아래 형식으로 추가됩니다:
    # "channel-id": {
    #     "enabled": True,
    #     "test_mode": True,
    #     "upload": False,
    #     "privacy": "private",
    #     "parallel": False,
    #     "allow_fallback": False,
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
    allow_fallback = channel_settings.get("allow_fallback", False)
    
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
                allow_fallback=allow_fallback
            )
        elif hasattr(pipeline_module, 'run'):
            pipeline_module.run(
                test_mode=is_test_mode,
                image_parallel=is_parallel,
                upload_to_youtube=should_upload,
                channel_id=channel_id,
                allow_fallback=allow_fallback
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
