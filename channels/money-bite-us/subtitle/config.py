"""
Money Bite 채널 자막 설정
자막 위치, 스타일, 폰트, 키워드 하이라이팅, 모드별 설정
"""

import os

# ============================================
# Screen Size (YouTube Shorts)
# ============================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


# ============================================
# Subtitle Position
# ============================================

# Y position ratio (based on screen height)
SUBTITLE_Y_RATIO = 0.55

# Actual Y position (pixels) - auto calculated
SUBTITLE_Y_POSITION = int(VIDEO_HEIGHT * SUBTITLE_Y_RATIO)


# ============================================
# Subtitle Style (공통)
# ============================================

# Font settings
FONT_DIR = os.path.join(os.getcwd(), "fonts")
SUBTITLE_FONT_PATH = os.path.join(FONT_DIR, "nanumsquare", "NanumSquareB.ttf")

# Subtitle width (with left/right margins)
SUBTITLE_MAX_WIDTH = 960

# Default colors
SUBTITLE_TEXT_COLOR = 'white'
SUBTITLE_STROKE_COLOR = 'black'
SUBTITLE_STROKE_WIDTH = 10
SUBTITLE_FONT_SIZE = 78  # 한국어 폰트 크기 (가독성 최적화)


# ============================================
# 모드별 설정
# ============================================

MODE_SETTINGS = {
    "static": {
        "font_size": 120,
        "typing_speed": 0.20,
        "min_chunk_chars": 0,      # 분리 불필요
        "max_width": 700,          # 줄바꿈 유도
    },
    "single": {
        "font_size": 110,
        "typing_speed": 0.3,
        "min_chunk_chars": 2,
    },
    "accumulate": {
        "font_size": 110,
        "typing_speed": 0.20,
        "min_chunk_chars": 2,
    },
    "stack": {
        "font_size": 110,
        "typing_speed": 0.5,
        "min_chunk_chars": 4,      # 짧은 어절 방지
    },
    "phrase": {
        "font_size": 85,          # 구절이 길어지므로 약간 작게
        "typing_speed": 0.3,
        "min_chunk_chars": 5,      # 한 구절 최소 5자
        "max_width": 960,          # 전체 폭 활용
    },
}

def get_mode_setting(subtitle_mode: str, key: str, default=None):
    """모드별 설정값을 가져옵니다."""
    settings = MODE_SETTINGS.get(subtitle_mode, MODE_SETTINGS["single"])
    return settings.get(key, default)


# ============================================
# Keyword Color Settings (금융 키워드)
# ============================================

# 1. Color Palette
COLOR_WARNING = '#FF3333'   # 빨강 (경고, 실수, 손실)
COLOR_EMPHASIS = '#FFD700'  # 골드 (돈, 수익, 핵심 수치)
COLOR_SECRET = '#00FF00'    # 초록 (팁, 수익, 긍정적)
COLOR_URGENT = '#00BFFF'    # 하늘색 (행동 유도, 시간 관련)

# 2. 키워드-카테고리 매핑 (한국어 금융 키워드)
KEYWORD_CATEGORIES = {
    'WARNING': [
        "절대", "하지마", "실수", "잘못", "위험", "폭락", "손해", "손실",
        "빚", "부채", "사기", "함정", "비싸", "고평가", "공포", "패닉",
        "망", "파산", "연체", "과소비",
    ],
    'EMPHASIS': [
        "반드시", "무조건", "핵심", "비밀", "최고", "최대", "중요",
        "기억", "명심", "필수", "100만", "1000만", "1억", "10억",
        "퍼센트", "%", "원", "수익", "이자", "배당", "수익률",
        "만원", "만 원", "천만", "조", "억",
    ],
    'SECRET': [
        "팁", "비법", "전략", "법칙", "방법", "공식", "규칙",
        "복리", "배당금", "인덱스", "포트폴리오", "분산", "ETF",
        "투자", "재테크", "적립식", "자산", "펀드", "지수",
        "주식", "채권", "부동산",
    ],
    'URGENT': [
        "지금", "오늘", "당장", "바로", "즉시", "빨리", "서둘러",
        "시간", "일찍", "먼저", "시작", "자동이체",
    ]
}

# 3. Category-Color Mapping
CATEGORY_COLORS = {
    'WARNING': COLOR_WARNING,
    'EMPHASIS': COLOR_EMPHASIS,
    'SECRET': COLOR_SECRET,
    'URGENT': COLOR_URGENT
}

def get_keyword_color(word: str, default_color: str = SUBTITLE_TEXT_COLOR) -> str:
    """키워드 매칭 시 하이라이트 색상 반환"""
    clean_word = word.replace('.', '').replace(',', '').replace('!', '').replace('?', '').strip()
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        for k in keywords:
            if clean_word.startswith(k) or clean_word == k:
                return CATEGORY_COLORS[category]
    
    return default_color

# Impact keywords (for special emphasis)
SUBTITLE_IMPACT_COLOR = '#FFD700'  # Gold
SUBTITLE_IMPACT_STROKE_WIDTH = 4

SUBTITLE_IMPACT_KEYWORDS = ["절대", "반드시", "비밀", "기억", "법칙", "핵심"]

# Pop-in 하이라이트 색상 (동적 자막에서 최신 어절 강조)
POPIN_HIGHLIGHT_COLOR = '#FFD700'


# ============================================
# Helper Functions
# ============================================

def get_subtitle_style(is_impactful: bool = False) -> dict:
    """Returns subtitle style settings as a dictionary."""
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
    """Checks if the text starts with an impact keyword."""
    words = text.split()
    if not words:
        return False
    first_word = words[0].strip('.,!?')
    return any(first_word.startswith(k) for k in SUBTITLE_IMPACT_KEYWORDS)
