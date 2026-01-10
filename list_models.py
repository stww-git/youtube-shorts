#!/usr/bin/env python3
"""
사용 가능한 Gemini/Imagen 모델 목록 출력

사용법:
    python3 list_models.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    print("   .env 파일에 GOOGLE_API_KEY=... 를 추가하세요.")
    exit(1)

genai.configure(api_key=api_key)

print("=" * 70)
print("📋 사용 가능한 모델 목록")
print("=" * 70)

for model in genai.list_models():
    name = model.name.replace("models/", "")
    methods = ", ".join(model.supported_generation_methods)
    print(f"\n🔹 {name}")
    print(f"   지원 메서드: {methods}")

print("\n" + "=" * 70)
