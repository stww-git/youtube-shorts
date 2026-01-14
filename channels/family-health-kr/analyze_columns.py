
import json
import sys
from pathlib import Path

# 현재 경로를 path에 추가하여 모듈 import 가능하게 함
sys.path.append(str(Path(__file__).parent))

from src.crawler import HealthColumnCrawler

def analyze_columns():
    crawler = HealthColumnCrawler()
    
    # 10개 칼럼 가져오기
    print("Collecting 10 columns for analysis...")
    columns = crawler.get_column_list(count=10)
    
    analyzed_data = []
    
    print("\n[Analysis Report]")
    for idx, col in enumerate(columns):
        print(f"\n--- Article {idx+1}: {col['title']} ---")
        detail = crawler.get_column_detail(col['article_id'], known_title=col['title'])
        
        if detail:
            content = detail['content']
            
            # 1. 길이
            length = len(content)
            
            # 2. 핵심 키워드 존재 여부
            has_warning = any(x in content for x in ["위험", "합병증", "사망", "주의", "심장", "뇌"])
            has_symptom = any(x in content for x in ["증상", "통증", "아픔", "신호"])
            has_solution = any(x in content for x in ["예방", "치료", "검사", "섭취", "운동"])
            
            print(f"   Length: {length} chars")
            print(f"   Structure: Warning={has_warning}, Symptom={has_symptom}, Solution={has_solution}")
            
            # 3. 앞부분(서론) 미리보기
            print(f"   Intro: {content[:100].replace(chr(10), ' ')}...")
            
            analyzed_data.append({
                "title": detail['title'],
                "content": content,
                "analysis": {
                    "has_warning": has_warning,
                    "has_symptom": has_symptom,
                    "has_solution": has_solution
                }
            })
    
    # 결과 저장 (프롬프트 튜닝 참고용)
    output_file = Path(__file__).parent / "analyzed_10_columns.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analyzed_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nFull analysis saved to {output_file}")

if __name__ == "__main__":
    analyze_columns()
