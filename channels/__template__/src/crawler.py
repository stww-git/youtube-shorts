"""
레시피 크롤러 모듈

10000recipe.com에서 레시피를 크롤링합니다.
"""

import os
import json
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from config.model_config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

# 카테고리 우선순위 (베스트 소진 후 순환)
CATEGORY_ORDER = [
    ("best", None),  # 전체 베스트
    ("밑반찬", "63"),
    ("국/탕", "54"),
    ("찌개", "55"),
    ("메인반찬", "56"),
    ("초스피드", "18"),  # 상황별 카테고리
    ("밥/죽/떡", "52"),
    ("면/만두", "53"),
    ("다이어트", "21"),  # 상황별 카테고리
]

from pathlib import Path

# 채널 폴더 내 히스토리 파일 (channels/{channel}/recipe_history.json)
CHANNEL_DIR = Path(__file__).parent.parent
HISTORY_FILE = CHANNEL_DIR / "history.json"


class RecipeCrawler:
    """10000recipe.com에서 레시피를 크롤링하는 클래스"""
    
    BASE_URL = "https://www.10000recipe.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    def _load_history(self) -> Dict:
        """히스토리 파일 로드"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
        return {"used_recipes": [], "last_updated": None}
    
    def _save_history(self, history: Dict):
        """히스토리 파일 저장"""
        dirname = os.path.dirname(HISTORY_FILE)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        history["last_updated"] = datetime.now().isoformat()
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def mark_as_used(self, recipe_id: str, title: str, category: str = "best", url: str = None):
        """레시피 사용 기록 저장"""
        history = self._load_history()
        if url is None:
            url = f"{self.BASE_URL}/recipe/{recipe_id}"
        history["used_recipes"].append({
            "recipe_id": recipe_id,
            "title": title,
            "category": category,
            "url": url,
            "used_at": datetime.now().strftime("%Y-%m-%d")
        })
        self._save_history(history)
        print(f"   📝 히스토리 저장: {title} (ID: {recipe_id})")
    
    def get_used_recipe_ids(self) -> set:
        """사용된 레시피 ID 목록 반환"""
        history = self._load_history()
        return {r["recipe_id"] for r in history.get("used_recipes", [])}
    
    def get_best_recipes(self, count: int = 50) -> List[Dict]:
        """베스트 레시피 목록 가져오기"""
        url = f"{self.BASE_URL}/ranking/home_new.html?rtype=r&dtype=d"
        return self._fetch_recipe_list(url, count, "best")
    
    def get_category_recipes(self, category_id: str, count: int = 50) -> List[Dict]:
        """카테고리별 레시피 목록 가져오기"""
        if category_id in ["18", "21"]:
            url = f"{self.BASE_URL}/recipe/list.html?cat2={category_id}&order=reco"
        else:
            url = f"{self.BASE_URL}/recipe/list.html?cat4={category_id}&order=reco"
        return self._fetch_recipe_list(url, count, category_id)
    
    def _fetch_recipe_list(self, url: str, count: int, category: str) -> List[Dict]:
        """레시피 목록 페이지 파싱 (재시도 로직 포함)"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                
                print(f"   🔍 레시피 목록 크롤링 중: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                recipes = []
                recipe_items = soup.find_all('li', class_='common_sp_list_li')
                
                if not recipe_items:
                    recipe_items = soup.find_all('li', class_=re.compile(r'(rcp|recipe|list)', re.I))
                
                for item in recipe_items:
                    link = item.find('a', href=re.compile(r'^/recipe/\d+$'))
                    if not link:
                        link = item.find('a', href=re.compile(r'/recipe/\d+'))
                    
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    recipe_match = re.search(r'/recipe/(\d+)', href)
                    if not recipe_match:
                        continue
                    
                    recipe_id = recipe_match.group(1)
                    
                    if any(r['recipe_id'] == recipe_id for r in recipes):
                        continue
                    
                    title = item.get_text(separator=' ', strip=True)
                    title_parts = title.split()
                    clean_title = []
                    for part in title_parts:
                        if part.isdigit() or '조회수' in part or '만' == part:
                            continue
                        clean_title.append(part)
                        if len(' '.join(clean_title)) > 30:
                            break
                    
                    title = ' '.join(clean_title)
                    
                    if not title or len(title) < 5:
                        continue
                    
                    if '구매' in title or '로그인' in title or title.startswith('http'):
                        continue
                    
                    recipes.append({
                        "recipe_id": recipe_id,
                        "title": title[:80],
                        "url": f"{self.BASE_URL}/recipe/{recipe_id}",
                        "category": category
                    })
                    
                    if len(recipes) >= count:
                        break
                
                if not recipes:
                    links = soup.find_all('a', href=re.compile(r'^/recipe/\d+$'))
                    for link in links[:min(count, 20)]:
                        href = link.get('href', '')
                        recipe_match = re.search(r'/recipe/(\d+)', href)
                        if recipe_match:
                            recipe_id = recipe_match.group(1)
                            if not any(r['recipe_id'] == recipe_id for r in recipes):
                                recipes.append({
                                    "recipe_id": recipe_id,
                                    "title": "",
                                    "url": f"{self.BASE_URL}/recipe/{recipe_id}",
                                    "category": category
                                })
                
                print(f"   ✅ {len(recipes)}개 레시피 발견")
                return recipes
                
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning(f"레시피 목록 크롤링 실패 (시도 {attempt}/{MAX_RETRIES}): {e}")
                    print(f"   ⚠️  크롤링 실패, 재시도 대기 중... ({RETRY_DELAY}초)")
                else:
                    logger.error(f"레시피 목록 크롤링 실패 ({MAX_RETRIES}회 시도 후): {e}")
                    print(f"   ❌ 크롤링 실패: {e}")
        
        return []
    
    def get_recipe_detail(self, recipe_id: str) -> Optional[Dict]:
        """레시피 상세 정보 가져오기 (재시도 로직 포함)"""
        url = f"{self.BASE_URL}/recipe/{recipe_id}"
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                
                print(f"   📖 레시피 상세 크롤링: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title_elem = soup.find('div', class_='view2_summary')
                title = ""
                if title_elem:
                    h3 = title_elem.find('h3')
                    title = h3.get_text(strip=True) if h3 else ""
                
                og_desc = soup.find('meta', property='og:description')
                description = og_desc.get('content', '') if og_desc else ""
                
                ingredients = []
                ing_list = soup.find('div', class_='ready_ingre3')
                if ing_list:
                    for li in ing_list.find_all('li'):
                        name_elem = li.find('a') or li
                        name = name_elem.get_text(strip=True)
                        amount_elem = li.find('span', class_='ingre_unit')
                        amount = amount_elem.get_text(strip=True) if amount_elem else ""
                        if name and not name.startswith('구매'):
                            ingredients.append({"name": name, "amount": amount})
                
                steps = []
                step_list = soup.find_all('div', class_='view_step_cont')
                for idx, step_div in enumerate(step_list, 1):
                    step_text = step_div.get_text(strip=True)
                    if step_text:
                        steps.append({"step": idx, "description": step_text})
                
                if not steps and description:
                    sentences = re.split(r'(?<=[.!?])\s+', description)
                    for idx, sent in enumerate(sentences[:8], 1):
                        if len(sent) > 10:
                            steps.append({"step": idx, "description": sent})
                
                result = {
                    "recipe_id": recipe_id,
                    "title": title,
                    "url": url,
                    "description": description,
                    "ingredients": ingredients,
                    "steps": steps
                }
                
                print(f"   ✅ 레시피 상세 로드 완료: {title}")
                print(f"      재료: {len(ingredients)}개, 조리단계: {len(steps)}개")
                
                return result
                
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning(f"레시피 상세 크롤링 실패 (시도 {attempt}/{MAX_RETRIES}): {e}")
                    print(f"   ⚠️  크롤링 실패, 재시도 대기 중... ({RETRY_DELAY}초)")
                else:
                    logger.error(f"레시피 상세 크롤링 실패 ({MAX_RETRIES}회 시도 후): {e}")
                    print(f"   ❌ 크롤링 실패: {e}")
        
        return None
    
    def get_next_recipe(self) -> Optional[Dict]:
        """다음에 사용할 레시피 자동 선택"""
        used_ids = self.get_used_recipe_ids()
        print(f"\n   📊 현재까지 사용한 레시피: {len(used_ids)}개")
        
        for category_name, category_id in CATEGORY_ORDER:
            print(f"\n   🔎 [{category_name}] 카테고리 탐색 중...")
            
            if category_id is None:
                recipes = self.get_best_recipes(100)
            else:
                recipes = self.get_category_recipes(category_id, 50)
            
            unused = [r for r in recipes if r['recipe_id'] not in used_ids]
            
            if unused:
                selected = unused[0]
                print(f"   ✅ 선택된 레시피: {selected['title']}")
                
                detail = self.get_recipe_detail(selected['recipe_id'])
                if detail:
                    detail['category'] = category_name
                    return detail
            else:
                print(f"   ⏭️  [{category_name}] 카테고리 소진, 다음으로 이동")
            
            time.sleep(0.5)
        
        print("\n   ⚠️  모든 레시피가 소진되었습니다!")
        return None


if __name__ == "__main__":
    crawler = RecipeCrawler()
    recipe = crawler.get_next_recipe()
    if recipe:
        print(f"\n=== 선택된 레시피 ===")
        print(f"제목: {recipe['title']}")
        print(f"재료: {', '.join([i['name'] for i in recipe['ingredients'][:5]])}...")
        print(f"조리단계: {len(recipe['steps'])}개")
