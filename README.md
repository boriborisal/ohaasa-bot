# 오하아사 운세 봇 (Oha-asa Horoscope Bot)

일본 TV 프로그램 "おはよう朝日です (Oha-asa)"의 오늘의 운세를 한국어로 번역하여 Discord에 제공하는 봇입니다.

## 주요 기능

- 📅 매일 업데이트되는 12개 별자리 운세
- 🇯🇵➡️🇰🇷 일본어 → 한국어 자동 번역
- ⚡ 1시간 캐싱으로 빠른 응답
- 🎨 별자리별 색상과 이모지가 적용된 이쁜 임베드 메시지
- 🔍 자동완성 기능으로 쉬운 별자리 선택

## 명령어

| 명령어 | 설명 |
|--------|------|
| `/운세 <별자리>` | 특정 별자리의 오늘 운세를 확인합니다 |
| `/오늘운세` | 12개 별자리 전체의 오늘 운세를 확인합니다 |
| `/도움말` | 봇 사용 방법을 확인합니다 |

## 지원하는 별자리

♈ 양자리, ♉ 황소자리, ♊ 쌍둥이자리, ♋ 게자리, ♌ 사자자리, ♍ 처녀자리,
♎ 천칭자리, ♏ 전갈자리, ♐ 사수자리, ♑ 염소자리, ♒ 물병자리, ♓ 물고기자리

---

## 설치 방법

### 1. 사전 준비

- Python 3.8 이상
- Discord 봇 토큰 (아래 "Discord 봇 생성하기" 참고)

### 2. 저장소 클론

```bash
git clone <repository-url>
cd ohaasa-bot
```

### 3. 가상환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. 의존성 설치

```bash
pip install -r requirements.txt
```

### 5. 환경 변수 설정

`.env` 파일을 열고 Discord 봇 토큰을 입력합니다:

```env
DISCORD_TOKEN=your_discord_bot_token_here
```

### 6. 봇 실행

```bash
python bot.py
```

봇이 정상적으로 실행되면 다음 메시지가 표시됩니다:

```
✅ [봇 이름] 봇이 온라인 상태입니다!
```

---

## Discord 봇 생성하기

### 1. Discord Developer Portal 접속

[Discord Developer Portal](https://discord.com/developers/applications)에 접속하여 로그인합니다.

### 2. 새 애플리케이션 생성

1. "New Application" 버튼 클릭
2. 봇 이름 입력 (예: "오하아사 운세 봇")
3. "Create" 클릭

### 3. 봇 생성

1. 왼쪽 메뉴에서 "Bot" 선택
2. "Add Bot" 버튼 클릭
3. "Yes, do it!" 클릭

### 4. 봇 토큰 복사

1. "TOKEN" 섹션에서 "Reset Token" 클릭
2. 생성된 토큰을 복사하여 `.env` 파일에 붙여넣기
3. ⚠️ **중요**: 토큰은 절대 공개하지 마세요!

### 5. 봇 권한 설정

1. "Privileged Gateway Intents" 섹션에서 다음 옵션 활성화:
   - ✅ MESSAGE CONTENT INTENT (선택사항)

### 6. OAuth2 URL 생성

1. 왼쪽 메뉴에서 "OAuth2" → "URL Generator" 선택
2. **SCOPES**에서 선택:
   - ✅ `bot`
   - ✅ `applications.commands`
3. **BOT PERMISSIONS**에서 선택:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Use Slash Commands
4. 하단에 생성된 URL 복사

### 7. 봇을 서버에 초대

1. 복사한 URL을 브라우저에 붙여넣기
2. 봇을 추가할 서버 선택
3. "Authorize" 클릭

---

## 프로젝트 구조

```
ohaasa-bot/
├── bot.py              # 메인 봇 진입점
├── scraper.py          # 오하아사 운세 페이지 스크래퍼
├── translator.py       # 일본어 → 한국어 번역 로직
├── config.py           # 설정 (토큰, API 키 등)
├── requirements.txt    # Python 의존성
├── .env                # 환경 변수 (Git에 커밋하지 않음)
└── README.md           # 이 파일
```

---

## 기술 스택

- **Discord.py** (v2.x) - Discord 봇 프레임워크
- **BeautifulSoup4** - HTML 파싱 및 스크래핑
- **Requests** - HTTP 요청
- **deep-translator** - 일본어 → 한국어 번역 (Google Translate 사용)
- **python-dotenv** - 환경 변수 관리

---

## 캐싱

운세 데이터는 **1시간 동안 메모리에 캐싱**됩니다. 이는 다음과 같은 이점을 제공합니다:

- ⚡ 빠른 응답 속도
- 🌐 웹사이트 서버 부하 감소
- 🔄 하루 중 운세는 변경되지 않으므로 충분한 캐시 시간

---

## 에러 처리

- **스크래핑 실패**: "현재 오하아사 사이트에서 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요. 🙏"
- **번역 실패**: 원본 일본어 텍스트 + "(번역 실패 — 원문)" 메시지 표시
- **모든 에러는 Python `logging` 모듈로 기록됨**

---

## 문제 해결

### 봇이 시작되지 않는 경우

1. `.env` 파일에 올바른 Discord 토큰이 설정되어 있는지 확인
2. 모든 의존성이 설치되어 있는지 확인: `pip install -r requirements.txt`
3. Python 버전이 3.8 이상인지 확인: `python --version`

### 슬래시 명령어가 표시되지 않는 경우

1. 봇이 서버에 올바르게 초대되었는지 확인 (`applications.commands` 스코프 포함)
2. 봇을 재시작한 후 최대 1시간까지 기다리기 (Discord가 명령어를 동기화하는 데 시간이 걸릴 수 있음)
3. 봇에게 필요한 권한이 부여되어 있는지 확인

### 운세 데이터를 불러올 수 없는 경우

1. 인터넷 연결 확인
2. 오하아사 웹사이트가 정상적으로 작동하는지 확인: https://www.asahi.co.jp/ohaasa/week/horoscope/index.html
3. 웹사이트 구조가 변경되었을 수 있음 → `scraper.py` 업데이트 필요

---

## 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로 제작되었습니다.

운세 데이터의 원본 출처: [おはよう朝日です (Oha-asa)](https://www.asahi.co.jp/ohaasa/)

---

## 기여

이슈 리포트 및 풀 리퀘스트를 환영합니다!

---

## 연락처

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**즐거운 하루 되세요! 🌟**
