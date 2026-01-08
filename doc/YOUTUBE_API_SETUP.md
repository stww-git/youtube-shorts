# 🎬 유튜브 자동 업로드를 위한 구글 클라우드 설정 가이드

YouTube 영상을 자동으로 업로드하기 위해서는 구글 클라우드에서 "프로젝트"를 만들고, 봇이 사용할 "출입증(API Key/Token)"을 발급받아야 합니다. 복잡해 보이지만 순서대로 따라오시면 됩니다!

---

## 1단계: 프로젝트 생성 및 API 켜기

1.  [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2.  상단 바에서 프로젝트 선택 목록(▼)을 클릭하고 **[새 프로젝트]**를 누릅니다.
    *   프로젝트 이름: `youtube-shorts-bot` (자유 설정)
    *   [만들기] 클릭
3.  알림이 뜨면 만든 프로젝트를 선택합니다.
4.  좌측 메뉴(≡) → **API 및 서비스** → **라이브러리**로 이동합니다.
5.  검색창에 `YouTube Data API v3`를 검색하고 클릭합니다.
6.  **[사용]** 버튼을 클릭합니다.

---

## 2단계: OAuth 동의 화면 구성 (딱 한 번만 설정)

API를 사용하려면 "이 앱은 이런 정보를 봅니다"라고 알려주는 화면 설정이 필요합니다.

1.  좌측 메뉴 → **API 및 서비스** → **OAuth 동의 화면**으로 이동합니다.
2.  **User Type**을 **[외부(External)]**로 선택하고 [만들기]를 클릭합니다.
3.  **앱 정보 입력:**
    *   앱 이름: `Shorts Uploader`
    *   사용자 지원 이메일: 본인 이메일 선택
    *   개발자 연락처 정보: 본인 이메일 입력
    *   나머지는 비워두고 맨 아래 **[저장 후 계속]**
4.  **범위(Scopes) 설정:**
    *   [범위 추가 또는 삭제] 클릭
    *   필터 검색창에 `youtube.upload` 검색
    *   `.../auth/youtube.upload` (YouTube 동영상 관리) 항목 체크 ✅
    *   [업데이트] → **[저장 후 계속]**
5.  **테스트 사용자:**
    *   **중요:** 아직 정식 앱이 아니므로, 본인 계정을 테스트 사용자로 등록해야 로그인이 됩니다.
    *   [+ ADD USERS] 클릭 → 본인 구글 이메일 입력 → [추가]
    *   **[저장 후 계속]**

---

## 3단계: 봇을 위한 ID/비밀번호(Credentials) 만들기

1.  좌측 메뉴 → **API 및 서비스** → **사용자 인증 정보(Credentials)**로 이동합니다.
2.  상단 **[+ 사용자 인증 정보 만들기]** → **OAuth 클라이언트 ID** 선택.
3.  **애플리케이션 유형:** **[데스크톱 앱]** 선택 (웹 애플리케이션 아님!)
    *   이름: `Local Login`
4.  **[만들기]** 클릭.
5.  팝업이 뜨면 **[JSON 다운로드]** 버튼을 눌러 파일을 받습니다.
    *   파일 이름을 `client_secrets.json`으로 바꾸고, 프로젝트 폴더 최상위(main_recipe.py 옆)에 넣습니다.

---

## 4단계: Refresh Token 발급받기 (로컬 실행)

이제 이 `client_secrets.json`을 이용해 로그인을 한 번 하고, **평생 쓸 수 있는 Refresh Token**을 받아야 합니다.

**[준비]**
터미널에서 필요한 라이브러리를 설치합니다:
```bash
pip install google-auth-oauthlib google-api-python-client
```

**[실행]**
제가 만들어드린 `src/upload/local_login.py`를 실행합니다:
```bash
python3 src/upload/local_login.py
```

**[로그인]**
1.  실행하면 인터넷 창이 열리고 구글 로그인 화면이 뜹니다.
2.  **"Google에서 확인하지 않은 앱"** 경고가 뜰 수 있습니다. (우리가 방금 만들어서 그렇습니다)
    *   좌측 하단 `고급(Advanced)` 클릭 → `Shorts Uploader(으)로 이동(안전하지 않음)` 클릭
3.  권한 요청 화면에서 **[허용]**을 계속 클릭합니다.
4.  "인증이 완료되었습니다" 창이 뜨면 창을 닫습니다.

**[결과 확인]**
터미널을 보면 아래와 같이 **Refresh Token**이 출력됩니다:
```text
✅ Refresh Token 발급 성공!
1//0gJ5... (이런 식으로 긴 문자열)
```

이 긴 문자열을 복사해 두세요! 이것이 **GitHub Actions의 비밀 열쇠**가 됩니다. 🔑

---

## 5단계: GitHub Secrets에 저장

이제 이 토큰을 GitHub에 안전하게 저장합니다.

1.  GitHub 저장소 페이지로 이동합니다.
2.  **Settings** → **Secrets and variables** → **Actions**
3.  **[New repository secret]** 클릭
4.  다음 3가지를 추가합니다:
    *   `CLIENT_ID`: `client_secrets.json` 파일 안의 `client_id` 값
    *   `CLIENT_SECRET`: `client_secrets.json` 파일 안의 `client_secret` 값
    *   `REFRESH_TOKEN`: 4단계에서 얻은 토큰 값

이제 준비 끝입니다! 봇이 이 정보를 이용해 영상을 업로드할 수 있습니다. 🚀
