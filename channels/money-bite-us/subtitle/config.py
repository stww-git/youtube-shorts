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
# Reduced width to avoid YouTube UI on the right
SUBTITLE_MAX_WIDTH = 800

# Default colors
SUBTITLE_TEXT_COLOR = 'white'
SUBTITLE_STROKE_COLOR = 'black'
SUBTITLE_STROKE_WIDTH = 10
SUBTITLE_FONT_SIZE = 70  # Reduced font size


# ============================================
# 모드별 설정
# ============================================

MODE_SETTINGS = {
    "static": {
        "font_size": 100,
        "typing_speed": 0.20,
        "min_chunk_chars": 0,      # 분리 불필요
        "max_width": 700,          # 줄바꿈 유도
    },
    "single": {
        "font_size": 100,
        "typing_speed": 0.3,
        "min_chunk_chars": 2,
    },
    "accumulate": {
        "font_size": 100,
        "typing_speed": 0.20,
        "min_chunk_chars": 2,
    },
    "stack": {
        "font_size": 100,
        "typing_speed": 0.5,
        "min_chunk_chars": 4,      # 짧은 어절 방지
    },
    "phrase": {
        "font_size": 70,          # 구절이 길어지므로 약간 작게
        "typing_speed": 0.3,
        "min_chunk_chars": 5,      # 한 구절 최소 5자
        "max_width": 800,          # 전체 폭 넓이 줄임 (UI 회피)
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
        "never", "don't", "mistake", "wrong", "risk", "crash", "loss", "lose",
        "debt", "scam", "trap", "expensive", "overvalued", "fear", "panic",
        "fail", "bankrupt", "delayed", "overspending", "warning",
    ],
    'EMPHASIS': [
        "must", "core", "secret", "best", "max", "important",
        "remember", "essential", "profit", "interest", "dividend", "yield", "critical",
    ],
    'SECRET': [
        "tip", "strategy", "rule", "method", "formula",
        "compound", "index", "portfolio", "diversify", "ETF",
        "invest", "wealth", "accumulate", "asset", "fund",
        "stock", "bond", "real estate",
    ],
    'URGENT': [
        "now", "today", "right now", "immediately", "fast", "hurry",
        "time", "early", "first", "start", "urgent",
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

SUBTITLE_IMPACT_KEYWORDS = ["never", "must", "secret", "remember", "rule", "core", "critical"]

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
