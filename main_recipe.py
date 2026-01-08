"""
레시피 기반 YouTube Shorts 자동 생성 시스템

10000recipe.com에서 레시피를 가져와 쇼츠 영상을 생성합니다.
"""

import argparse
import warnings
from dotenv import load_dotenv

from src.pipeline import RecipeVideoPipeline
from src.utils import print_header, check_environment

# Suppress ALL warnings before importing other modules
warnings.filterwarnings('ignore')
import logging
logging.captureWarnings(True)

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress urllib3 warnings
try:
    import urllib3
    urllib3.disable_warnings()
except:
    pass

# Load environment variables
load_dotenv()

# ==========================================
# 사용자 설정 (User Configuration)
# ==========================================
# 테스트 모드 (이미지 생성 건너뛰기)
# True로 설정하면 --test 옵션 없이도 항상 테스트 모드로 실행됩니다.
TEST_MODE = True

# 이미지 생성 병렬 처리 (True: 빠름, False: 안정적)
# API Rate Limit 오류가 발생하면 False로 설정하세요.
IMAGE_PARALLEL = False



def main():
    print_header("🍳 YouTube Shorts 자동 생성 시스템 (Recipe-Based)")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='YouTube Shorts Generator')
    parser.add_argument('--test', action='store_true', help='Test mode: use placeholder images instead of generating new ones')
    args = parser.parse_args()
    
    # Check both CLI arg and global constant
    is_test_mode = args.test or TEST_MODE
    
    if is_test_mode:
        print("\n   🧪 [TEST MODE ENABLED] 이미지 생성을 건너뛰고 플레이스홀더를 사용합니다.\n")
    
    check_environment()
    
    # Initialize and run pipeline
    # Initialize and run pipeline
    pipeline = RecipeVideoPipeline()
    pipeline.run(test_mode=is_test_mode, image_parallel=IMAGE_PARALLEL)



if __name__ == "__main__":
    main()
