"""
Prompt Debug Logger
프롬프트 입력/출력을 파일로 저장하는 유틸리티
"""
import os
from datetime import datetime
from pathlib import Path


class PromptDebugLogger:
    """프롬프트 디버그 로거 - 각 단계별 입력/프롬프트/출력을 기록"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir
        self.logs = []
        self.start_time = datetime.now()
        
    def set_output_dir(self, output_dir: str):
        """출력 디렉토리 설정"""
        self.output_dir = output_dir
        
    def log_raw_data(self, data: dict, data_type: str = "레시피"):
        """크롤링 원본 데이터 기록 (전체 데이터)"""
        section = f"""
## 1. 크롤링 원본 데이터 ({data_type})

"""
        for key, value in data.items():
            if isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # 모든 딕셔너리 리스트는 JSON으로 출력 (재료, steps 등)
                    import json
                    formatted = json.dumps(value, ensure_ascii=False, indent=2)
                elif value and isinstance(value[0], str):
                    # 문자열 리스트 - 전체 줄바꿈 출력
                    formatted = "\n".join([f"- {v}" for v in value])
                else:
                    # 기타 리스트
                    import json
                    formatted = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                formatted = str(value)
            section += f"### {key}\n```\n{formatted}\n```\n\n"
        
        self.logs.append(section)
        
    def log_prompt_step(self, step_num: int, step_name: str, 
                        input_data: str, prompt_template: str, 
                        output_data: str, prompt_name: str = ""):
        """프롬프트 단계 기록 (전체 데이터, 잘림 없음)"""
        
        section = f"""
---
## {step_num}. {step_name}

### 📥 입력 데이터
```
{input_data}
```

### 📝 프롬프트 ({prompt_name})
```
{prompt_template}
```

### 📤 출력 결과
```
{output_data}
```
"""
        self.logs.append(section)
        
    def save(self, filename: str = "prompt_debug.md"):
        """로그 파일 저장"""
        if not self.output_dir:
            print("   ⚠️ 출력 디렉토리가 설정되지 않아 프롬프트 로그를 저장하지 않습니다.")
            return None
            
        # 헤더 생성
        header = f"""# 🔍 프롬프트 디버그 로그

**생성 시각**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}  
**출력 폴더**: `{self.output_dir}`

이 파일은 영상 생성 과정에서 사용된 모든 프롬프트의 입력/출력을 기록합니다.

"""
        
        # 전체 내용 조합
        content = header + "\n".join(self.logs)
        
        # 파일 저장
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"   📝 프롬프트 디버그 로그 저장: {filepath}")
        return filepath


# 전역 로거 인스턴스 (싱글톤 패턴)
_debug_logger = None

def get_prompt_logger() -> PromptDebugLogger:
    """전역 프롬프트 로거 반환"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = PromptDebugLogger()
    return _debug_logger

def reset_prompt_logger():
    """프롬프트 로거 초기화"""
    global _debug_logger
    _debug_logger = PromptDebugLogger()
    return _debug_logger
