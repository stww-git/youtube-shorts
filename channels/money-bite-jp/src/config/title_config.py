"""
영상 제목 설정 파일 (Title Configuration)

제목의 폰트, 스타일, 적응형 크기 로직 등을 관리합니다.
"""
import os

# ============================================
# 폰트 설정
# ============================================
FONT_DIR = os.path.join(os.getcwd(), "fonts")
TITLE_FONT_PATH = os.path.join(FONT_DIR, "notosansjp", "NotoSansJP-Bold.ttf")

# ============================================
# 기본 스타일
# ============================================
TITLE_TEXT_COLOR = 'white'
# 줄별 색상 설정 (None이면 기본 색상 사용)
TITLE_LINE_COLORS = ['#FFFFFF', '#FFD54F']  # 1줄: White, 2줄: Warm Yellow
TITLE_STROKE_COLOR = 'black'
TITLE_STROKE_WIDTH = 0  # 테두리 없음
TITLE_FONT_SIZE = 120     # 기본 폰트 크기

# 자간 설정 (단위: px)
# 기준: 폰트 크기 100px 일 때
# - 0: 기본값 (정직한 간격)
# - -5 ~ -10 (5~10%): 깔끔한 제목 (세련된 느낌)
# - -20 ~ -30 (20~30%): 임팩트형 제목 (꽉 찬 느낌, 현재 설정)
TITLE_LETTER_SPACING = 0

TITLE_MAX_WIDTH = 800     # 최대 너비
TITLE_LINE_HEIGHT = 1.0   # 줄간격 배수 (1.0 = 빼곡하게)

TITLE_TOP_MARGIN = 110     # 제목 텍스트 Y 위치 (제목만 이동)
TITLE_BG_TOP_MARGIN = 100  # 검은색 배경 높이 계산용 (배경 크기 조절)

# ============================================
# 적응형 폰트 크기 설정 (Adaptive Font Sizing)
# ============================================
# 제목 길이에 따른 폰트 크기 및 줄간격 배수
TITLE_SIZE_RULES = [
    # (글자수 미만, 폰트크기, 줄간격배수)
    (15, 120, 1.2),
    (25, 100, 1.25),
    (999, 80, 1.3)  # 기본값 (나머지 긴 제목)
]

def get_adaptive_title_style(text_len: int):
    """
    제목 길이에 맞는 폰트 크기와 줄간격 배수를 반환합니다.
    
    Args:
        text_len (int): 제목 글자 수
        
    Returns:
        tuple: (font_size, line_height_factor)
    """
    for limit, size, height in TITLE_SIZE_RULES:
        if text_len < limit:
            return size, height
    return 80, 1.3
