"""
Money Bite 토픽 선택기

terms.json에서 순서대로 다음 용어를 선택합니다.
사용한 용어는 히스토리에 기록하여 중복을 방지합니다.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHANNEL_DIR = Path(__file__).parent.parent
TERMS_FILE = CHANNEL_DIR / "terms.json"

def _get_history_file():
    import os
    if os.getenv("GITHUB_ACTIONS"):
        return CHANNEL_DIR / "history.json"
    return CHANNEL_DIR / "history.local.json"

HISTORY_FILE = _get_history_file()


class TopicGenerator:
    """terms.json에서 순서대로 용어를 선택하는 토픽 선택기"""
    
    def __init__(self):
        self.api_call_count = 0
        logger.info("TopicGenerator initialized (list-based)")

    def get_api_call_count(self):
        return self.api_call_count

    def _load_terms(self) -> list:
        """terms.json에서 용어 목록 로드"""
        if not TERMS_FILE.exists():
            logger.error(f"terms.json not found: {TERMS_FILE}")
            return []
        with open(TERMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_history(self) -> dict:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"used_topics": []}
        return {"used_topics": []}
    
    def _save_history(self, history: dict):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _get_used_terms(self) -> set:
        """히스토리에서 사용한 용어 목록 추출"""
        history = self._load_history()
        used_topics = history.get("used_topics", history.get("used_recipes", []))
        return {t.get("term", t.get("title", "")) for t in used_topics}

    def get_next_topic(self) -> dict:
        """
        terms.json에서 다음 미사용 용어를 순서대로 선택합니다.
        
        Returns:
            {"term": "PER 쉽게 설명"} 또는 None (모두 사용 시)
        """
        terms = self._load_terms()
        if not terms:
            print("   ❌ terms.json을 찾을 수 없거나 비어있습니다.")
            return None

        used = self._get_used_terms()
        
        for term in terms:
            if term not in used:
                print(f"\n   📌 선택된 용어: {term}")
                print(f"   📊 진행률: {len(used)}/{len(terms)}개 완료")
                return {"term": term}
        
        # 모든 용어 사용 완료
        print(f"\n   ✅ 모든 키워드({len(terms)}개)에 대해 영상을 생성했습니다!")
        print(f"   terms.json에 새로운 용어를 추가하면 계속 생성할 수 있습니다.")
        return None

    def mark_as_used(self, term: str, video_title: str):
        """사용한 용어를 히스토리에 기록"""
        history = self._load_history()
        if "used_topics" not in history:
            history["used_topics"] = history.get("used_recipes", [])
        history["used_topics"].append({
            "term": term,
            "video_title": video_title,
            "used_at": datetime.now().isoformat()
        })
        self._save_history(history)
        logger.info(f"Marked as used: {term} -> {video_title}")


if __name__ == "__main__":
    generator = TopicGenerator()
    topic = generator.get_next_topic()
    if topic:
        print(f"다음 용어: {topic['term']}")
    else:
        print("모든 용어 사용 완료")
