"""
자막 설정 파일 (Subtitle Configuration)

자막의 위치, 스타일, 폰트 등을 한 곳에서 관리합니다.
자막을 수정하려면 이 파일만 수정하면 됩니다.
"""

import os

# ============================================
# 화면 크기 (YouTube Shorts)
# ============================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


# ============================================
# 자막 위치 설정
# ============================================

# Y 위치 비율 (화면 높이 기준)
# 0.4: 화면 위쪽 (40%)
# 0.5: 정중앙 (50%)
# 0.55: 기본값 - 중앙 약간 아래 (55%)
# 0.7: 화면 아래쪽 (70%)
SUBTITLE_Y_RATIO = 0.55

# 실제 Y 위치 (픽셀) - 자동 계산
SUBTITLE_Y_POSITION = int(VIDEO_HEIGHT * SUBTITLE_Y_RATIO)


# ============================================
# 자막 스타일 설정
# ============================================

# 폰트 설정
FONT_DIR = os.path.join(os.getcwd(), "fonts")
SUBTITLE_FONT_PATH = os.path.join(FONT_DIR, "nanumsquare", "NanumSquareB.ttf")

# 자막 너비 (좌우 여백 포함)
# 1080px 화면에서 960px = 좌우 60px 여백
SUBTITLE_MAX_WIDTH = 960

# 기본 색상
SUBTITLE_TEXT_COLOR = 'white'
SUBTITLE_STROKE_COLOR = 'black'
SUBTITLE_STROKE_WIDTH = 10
SUBTITLE_FONT_SIZE = 80  # 기본 자막 폰트 크기

# ============================================
# 키워드별 색상 설정 (Intonation-based Coloring)
# ============================================

# 1. 색상 팔레트
COLOR_WARNING = '#FF3333'  # 밝은 빨강 (강한 경고/금지)
COLOR_EMPHASIS = '#FFD700' # 금색 (긍정/감탄/강조)
COLOR_SECRET = '#00FF00'   # 밝은 라임/녹색 (비법/해결책)
COLOR_URGENT = '#FF00FF'   # 마젠타/핑크 (긴급/속보)

# 2. 키워드 카테고리 매핑
KEYWORD_CATEGORIES = {
    'WARNING': [
        "절대", "경고", "금지", "조심", "주의", "망함", "큰일", "제발", "최악", "위험",
        "넣지", "하지", "쓰지", "마세요"  # 부정어구 추가
    ],
    'EMPHASIS': [
        "무조건", "평생", "인생", "대박", "진짜", "정말", "완전", "최고", "깜짝", "특히", "와"
    ],
    'SECRET': [
        "비밀", "정답", "비법", "핵심", "필수", "강추", "추천", "꿀팁", "노하우", "공개"
    ],
    'URGENT': [
        "지금", "바로", "당장", "속보", "빨리", "어서"
    ]
}

# 3. 카테고리별 색상 매핑
CATEGORY_COLORS = {
    'WARNING': COLOR_WARNING,
    'EMPHASIS': COLOR_EMPHASIS,
    'SECRET': COLOR_SECRET,
    'URGENT': COLOR_URGENT
}

def get_keyword_color(word: str, default_color: str = SUBTITLE_TEXT_COLOR) -> str:
    """
    단어가 특정 카테고리 키워드로 시작하면 해당 색상을 반환합니다.
    
    Args:
        word: 검사할 단어
        default_color: 매칭되는 키워드가 없을 때 반환할 색상
        
    Returns:
        Hex 색상 코드
    """
    clean_word = word.replace('.', '').replace(',', '').replace('!', '').replace('?', '').strip()
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        for k in keywords:
            if clean_word.startswith(k):
                return CATEGORY_COLORS[category]
    
    return default_color

# 강조 색상 (impact keywords)
SUBTITLE_IMPACT_COLOR = '#FFD700'  # 금색
SUBTITLE_IMPACT_STROKE_WIDTH = 4

# 강조 키워드 목록
SUBTITLE_IMPACT_KEYWORDS = ["절대", "경고", "비밀", "정답", "비법"]


# ============================================
# 편의 함수
# ============================================

def get_subtitle_style(is_impactful: bool = False) -> dict:
    """
    자막 스타일 설정을 딕셔너리로 반환합니다.
    
    Args:
        is_impactful: 강조 키워드 여부
    
    Returns:
        스타일 설정 딕셔너리
    """
    return {
        'font_size': SUBTITLE_FONT_SIZE,
        'font_path': SUBTITLE_FONT_PATH,
        'text_color': SUBTITLE_IMPACT_COLOR if is_impactful else SUBTITLE_TEXT_COLOR,
        'stroke_color': SUBTITLE_STROKE_COLOR,
        'stroke_width': SUBTITLE_IMPACT_STROKE_WIDTH if is_impactful else SUBTITLE_STROKE_WIDTH,
        'max_width': SUBTITLE_MAX_WIDTH,
        'y_position': SUBTITLE_Y_POSITION,
    }


def is_impact_text(text: str) -> bool:
    """
    텍스트가 강조 키워드로 시작하는지 확인합니다.
    
    Args:
        text: 확인할 텍스트
    
    Returns:
        강조 키워드로 시작하면 True
    """
    words = text.split()
    if not words:
        return False
    first_word = words[0]
    return any(first_word.startswith(k) for k in SUBTITLE_IMPACT_KEYWORDS)
