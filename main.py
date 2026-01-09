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

# 1. 타겟 채널 설정 (Target Channel)
#    - channels/ 폴더 내에 있는 채널 ID (폴더명)를 입력하세요.
#    - 예: "sokpyeonhan", "sample_channel"
TARGET_CHANNEL = "test-channel-trial1"

# 2. 동작 모드 설정 (Operation Modes)
#    - TEST_MODE: True일 경우 이미지 생성 등을 건너뛰고 빠르게 로직만 검증합니다.
TEST_MODE = True

#    - UPLOAD_TO_YOUTUBE: True일 경우 영상 생성 후 자동으로 유튜브에 업로드합니다.
#    - 주의: '.env' 파일에 해당 채널의 인증 정보가 설정되어 있어야 합니다.
UPLOAD_TO_YOUTUBE = True

# 3. 성능 설정 (Performance)
#    - IMAGE_PARALLEL: 이미지 생성을 병렬로 처리하여 속도를 높입니다.
#    - 주의: API 사용량 제한(Quota)이 낮을 경우 False로 설정하세요.
IMAGE_PARALLEL = False

# ==============================================================================





def main():
    print_header("🎬 YouTube Shorts 자동 생성 시스템")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='YouTube Shorts Generator')
    parser.add_argument('--test', action='store_true', help='Test mode')
    parser.add_argument('--upload', action='store_true', help='Upload to YouTube')
    parser.add_argument('--channel', type=str, default=None, help='Target channel ID')
    args = parser.parse_args()
    
    # 설정 결정
    is_test_mode = args.test or TEST_MODE
    should_upload = args.upload or UPLOAD_TO_YOUTUBE
    channel_id = args.channel if args.channel else TARGET_CHANNEL
    

    
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
                image_parallel=IMAGE_PARALLEL,
                upload_to_youtube=should_upload,
                channel_id=channel_id
            )
        elif hasattr(pipeline_module, 'run'):
            pipeline_module.run(
                test_mode=is_test_mode,
                image_parallel=IMAGE_PARALLEL,
                upload_to_youtube=should_upload,
                channel_id=channel_id
            )
        else:
            print(f"   ❌ 채널 '{channel_id}'의 pipeline에 실행 가능한 함수가 없습니다.")
            
    except FileNotFoundError as e:
        print(f"   ❌ {e}")
    except Exception as e:
        print(f"   ❌ 파이프라인 실행 오류: {e}")
        raise


if __name__ == "__main__":
    main()
