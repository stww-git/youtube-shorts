#!/usr/bin/env python3
"""
Vertex AI에서 사용 가능한 Gemini/Imagen 모델 목록 출력

사용법:
    python3 list_models.py
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
location = os.getenv("GCP_LOCATION", "us-central1")

client = genai.Client(vertexai=True, project=project_id, location=location)

print("=" * 70)
print(f"📋 Gemini & Imagen 모델 목록 (Vertex AI: {project_id})")
print("=" * 70)

# 카테고리별 분류
categories = {
    "📝 Text (Gemini)": [],
    "🖼️ Image (Imagen)": [],
    "🖼️ Image (Gemini)": [],
    "🎤 TTS": [],
    "🔗 Embedding": [],
    "🎬 Video (Veo)": [],
    "🛡️ Safety": [],
    "🤖 기타 Gemini/Gemma": [],
}

for model in client.models.list():
    name = model.name.replace("publishers/google/models/", "")
    
    # Gemini/Imagen/Veo/Gemma 관련만 필터
    if not any(k in name.lower() for k in ["gemini", "imagen", "gemma", "veo", "embedding"]):
        continue
    
    # 카테고리 분류
    if "tts" in name.lower():
        categories["🎤 TTS"].append(name)
    elif "imagen" in name.lower():
        categories["🖼️ Image (Imagen)"].append(name)
    elif "image" in name.lower() and "gemini" in name.lower():
        categories["🖼️ Image (Gemini)"].append(name)
    elif "veo" in name.lower():
        categories["🎬 Video (Veo)"].append(name)
    elif "embedding" in name.lower():
        categories["🔗 Embedding"].append(name)
    elif "shield" in name.lower():
        categories["🛡️ Safety"].append(name)
    elif "gemma" in name.lower():
        categories["🤖 기타 Gemini/Gemma"].append(name)
    elif "gemini" in name.lower():
        categories["📝 Text (Gemini)"].append(name)
    else:
        categories["🤖 기타 Gemini/Gemma"].append(name)

for category, models in categories.items():
    if not models:
        continue
    print(f"\n{category} ({len(models)}개)")
    print("-" * 50)
    for m in sorted(models):
        # GA vs Preview 표시
        tag = "🏷️ preview" if "preview" in m else "✅ GA"
        print(f"  {m:<50} {tag}")

print("\n" + "=" * 70)
print("💡 참고: 목록에 있어도 프로젝트 권한에 따라 호출 불가능할 수 있습니다.")
print("   GA 모델은 대부분 바로 사용 가능, preview는 별도 신청이 필요할 수 있습니다.")
print("=" * 70)
