"""
NHIS 전문가칼럼 크롤러
국민건강보험공단 건강 새소식 > 전문가칼럼에서 건강 정보를 가져옵니다.
"""

import json
import logging
import os
import re
import time
from typing import Dict, List, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 로깅 설정
logger = logging.getLogger(__name__)

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2

# 히스토리 파일 경로
# - GitHub Actions (원격): history.json (Git 추적)
# - 로컬 환경: history.local.json (Git 무시)
def _get_history_file():
    """환경에 따라 히스토리 파일 경로 반환"""
    channel_dir = Path(__file__).parent.parent
    if os.getenv('GITHUB_ACTIONS') == 'true':
        return channel_dir / "history.json"
    else:
        return channel_dir / "history.local.json"

HISTORY_FILE = _get_history_file()


class HealthColumnCrawler:
    """NHIS 전문가칼럼 크롤러"""
    
    BASE_URL = "https://www.nhis.or.kr"
    LIST_URL = "/nhis/healthin/wbhace05200m01.do"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    def get_used_article_ids(self) -> set:
        """이미 사용한 칼럼 ID 목록 반환"""
        if not HISTORY_FILE.exists():
            return set()
        
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                return set(history.get("used_article_ids", []))
        except Exception as e:
            logger.warning(f"히스토리 로드 실패: {e}")
            return set()
    
    def save_used_article_id(self, article_id: str, title: str = ""):
        """사용한 칼럼 ID 및 제목 저장"""
        history = {"used_article_ids": [], "article_titles": {}}
        
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
        
        if "used_article_ids" not in history:
            history["used_article_ids"] = []
            
        if "article_titles" not in history:
            history["article_titles"] = {}
        
        if article_id not in history["used_article_ids"]:
            history["used_article_ids"].append(article_id)
            
        if title:
            history["article_titles"][article_id] = title
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_column_list(self, count: int = 50) -> List[Dict]:
        """전문가칼럼 목록 가져오기"""
        columns = []
        offset = 0
        
        print(f"\n   📋 [전문가칼럼 목록 크롤링]")
        
        while len(columns) < count:
            url = f"{self.BASE_URL}{self.LIST_URL}?mode=list&article.offset={offset}&articleLimit=10"
            
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    if attempt > 1:
                        print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                    
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 칼럼 링크 찾기
                    links = soup.find_all('a', href=re.compile(r'mode=view&articleNo=\d+'))
                    
                    if not links:
                        break
                    
                    for link in links:
                        href = link.get('href', '')
                        match = re.search(r'articleNo=(\d+)', href)
                        if match:
                            article_id = match.group(1)
                            title = link.get_text(strip=True)
                            
                            if title and len(title) > 2:
                                columns.append({
                                    "article_id": article_id,
                                    "title": title,
                                    "url": f"{self.BASE_URL}{self.LIST_URL}?mode=view&articleNo={article_id}"
                                })
                    
                    break
                    
                except Exception as e:
                    if attempt == MAX_RETRIES:
                        logger.error(f"목록 크롤링 실패: {e}")
                        print(f"   ❌ 크롤링 실패: {e}")
                        
                        # 첫 페이지에서 모든 재시도 실패 시 예외 발생 (네트워크 문제로 판단)
                        if offset == 0:
                            raise Exception(f"네트워크 연결 실패! 인터넷 연결을 확인해주세요. (원인: {e})")
            
            offset += 10
            if offset > 60:  # 최대 7페이지
                break
            
            time.sleep(0.5)
        
        # 중복 제거
        seen = set()
        unique_columns = []
        for col in columns:
            if col['article_id'] not in seen:
                seen.add(col['article_id'])
                unique_columns.append(col)
        
        print(f"   ✅ {len(unique_columns)}개 칼럼 발견")
        return unique_columns[:count]
    
    def get_column_detail(self, article_id: str, known_title: str = "") -> Optional[Dict]:
        """칼럼 상세 정보 가져오기"""
        url = f"{self.BASE_URL}{self.LIST_URL}?mode=view&articleNo={article_id}"
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                
                print(f"   📖 칼럼 상세 크롤링: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 제목 추출 (이미 알고 있는 제목 우선 사용)
                title = known_title
                if not title:
                    title_elem = soup.find('h3', class_='view_title') or soup.find('h3') or soup.find('h2')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # 메타 정보 추출 (출처, 집필자, 날짜)
                source = ""
                author = ""
                date = ""
                
                # 출처 찾기
                source_elem = soup.find(string=re.compile(r'출처'))
                if source_elem:
                    parent = source_elem.find_parent()
                    if parent:
                        source = parent.get_text(strip=True).replace('출처', '').strip()
                
                # 집필자 찾기
                author_elem = soup.find(string=re.compile(r'집필자'))
                if author_elem:
                    parent = author_elem.find_parent()
                    if parent:
                        author = parent.get_text(strip=True).replace('집필자', '').strip()
                
                # 본문 추출
                content_parts = []
                
                # 본문 영역 추출 (다양한 방법 시도)
                content_area = soup.find('div', class_='bbs_cont') or soup.find('div', class_='view_cont')
                
                if content_area:
                    # 모든 텍스트 추출
                    for elem in content_area.find_all(['p', 'div', 'li']):
                        text = elem.get_text(strip=True)
                        if text and len(text) > 10:
                            content_parts.append(text)
                
                # 본문이 없으면 전체 페이지에서 추출
                if not content_parts:
                    for p in soup.find_all('p'):
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:
                            content_parts.append(text)
                
                content = "\n\n".join(content_parts[:20])  # 최대 20개 단락
                
                if not title or not content:
                    print(f"   ⚠️ 내용 추출 실패")
                    return None
                
                result = {
                    "article_id": article_id,
                    "title": title,
                    "source": source,
                    "author": author,
                    "date": date,
                    "content": content,
                    "url": url
                }
                
                print(f"   ✅ 칼럼 로드 완료: {title}")
                print(f"      출처: {source}, 집필자: {author}")
                print(f"      본문 길이: {len(content)}자")
                
                return result
                
            except Exception as e:
                if attempt == MAX_RETRIES:
                    logger.error(f"칼럼 상세 크롤링 실패: {e}")
                    print(f"   ❌ 크롤링 실패: {e}")
        
        return None
    
    def get_next_column(self) -> Optional[Dict]:
        """다음에 사용할 칼럼 자동 선택"""
        used_ids = self.get_used_article_ids()
        print(f"\n   📊 현재까지 사용한 칼럼: {len(used_ids)}개")
        
        # 칼럼 목록 가져오기
        columns = self.get_column_list(50)
        
        # 제외할 키워드 (너무 전문적이거나 정책적인 내용)
        BLACKLIST_KEYWORDS = [
            "빅데이터", "4.0", "구축", "표준화", "시스템", "정책", 
            "통계", "현황", "워크숍", "학회", "포럼", "심포지엄",
            "MOU", "체결", "협약", "시범사업", "토론회"
        ]
        
        # 미사용 칼럼 찾기
        for col in columns:
            if col['article_id'] not in used_ids:
                # 1차 제목 필터링
                title = col['title']
                if any(keyword in title for keyword in BLACKLIST_KEYWORDS):
                    print(f"   🚫 스킵 (전문/정책 콘텐츠): {title}")
                    # 스킵된 것도 사용한 것으로 처리하여 다시 확인하지 않음
                    self.save_used_article_id(col['article_id'], title)
                    continue
                
                print(f"\n   ✅ 선택된 칼럼: {title}")
                
                # 상세 정보 가져오기 (제목 전달)
                detail = self.get_column_detail(col['article_id'], known_title=title)
                if detail:

                        
                    # 사용 기록 저장
                    self.save_used_article_id(col['article_id'], title)
                    return detail
        
        print("\n   ⚠️ 모든 칼럼이 소진되었습니다!")
        return None


if __name__ == "__main__":
    crawler = HealthColumnCrawler()
    column = crawler.get_next_column()
    
    if column:
        print(f"\n{'='*60}")
        print(f"=== 선택된 칼럼 ===")
        print(f"{'='*60}")
        print(f"제목: {column['title']}")
        print(f"출처: {column['source']}")
        print(f"집필자: {column['author']}")
        print(f"URL: {column['url']}")
        print(f"\n본문 미리보기:")
        print(column['content'][:500] + "..." if len(column['content']) > 500 else column['content'])
