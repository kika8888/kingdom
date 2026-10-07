# KINGDOM

노트북을 꺼도 GitHub 서버에서 24시간 돌아갑니다. 비용은 무료입니다.

모든 자동 작업은 `.github/workflows/kingdom.yml` 하나에 들어 있습니다. 직접 실행할 때는 **Actions › KINGDOM › Run workflow** 에서 task 를 고릅니다 (collect 상품 수집, threads 스레드 게시, report 수익 알림, link 링크 만들기, token-refresh 토큰 갱신).

| 작업 | 언제 | 결과 |
|---|---|---|
| 상품 수집 | 매시간 | 골드박스, 카테고리 베스트, 관심 키워드 상품을 내 파트너스 링크로 모은 웹페이지 |
| 스레드 게시 | 4시간마다 (하루 6개) | 잘 팔리는 상품을 골라 사진·가격·링크로 스레드에 올림 |
| 토큰 갱신 | 매주 | 스레드 토큰이 만료되지 않게 갱신 |
| 수익 알림 | 매일 오전 9시 | 어제 클릭·주문·수익을 텔레그램으로 받음 |
| 링크 만들기 | 원할 때 | 쿠팡 상품 주소를 파트너스 링크로 변환 |

## 1. 저장소 만들기

1. github.com 오른쪽 위 **+** › **New repository**
2. 이름 예: `kingdom`, **Public** 선택 (무료로 웹페이지를 보려면 Public이어야 합니다. API 키와 수익은 공개되지 않습니다)
3. **Create repository**
4. 화면의 **uploading an existing file** 링크를 누르고, 이 폴더 안의 파일과 폴더(`.github`, `docs`, `*.py`, `README.md`)를 전부 끌어다 놓은 뒤 **Commit changes**
   - `.github` 폴더가 꼭 들어가야 합니다. 올린 뒤 저장소에 `.github/workflows` 가 보이는지 확인하세요.

## 2. API 키 넣기 (비밀값)

저장소 **Settings › Secrets and variables › Actions › Secrets** 탭 › **New repository secret**

| 이름 | 값 |
|---|---|
| `COUPANG_ACCESS_KEY` | 파트너스 Access Key |
| `COUPANG_SECRET_KEY` | 파트너스 Secret Key |
| `TELEGRAM_BOT_TOKEN` | (선택) 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | (선택) 내 텔레그램 채팅 ID |
| `THREADS_ACCESS_TOKEN` | 스레드 장기 토큰 (아래 '스레드 연결' 참고) |
| `GH_PAT` | 스레드 토큰 자동 갱신용 GitHub 토큰 (아래 참고) |

같은 화면 **Variables** 탭 (공개돼도 괜찮은 설정)

| 이름 | 예시 |
|---|---|
| `SEARCH_KEYWORDS` | `캠핑의자, 무선청소기, 에어프라이어` (최대 3개) |
| `PARTNERS_SUB_ID` | (선택) `threads` 처럼 채널 구분용. 넣으면 실적에서 스레드 수익만 따로 볼 수 있습니다 |
| `BEST_CATEGORIES` | (선택) 올릴 분야만 고르기. 예: `1012,1014,1016` (식품, 생활용품, 가전디지털). 비우면 전체 |

## 3. 권한과 웹페이지 켜기

1. **Settings › Actions › General** 맨 아래 **Workflow permissions** › **Read and write permissions** 선택 › Save
2. **Settings › Pages** › Branch 를 `main`, 폴더를 `/docs` 로 › Save
3. 몇 분 뒤 `https://내아이디.github.io/kingdom/` 에서 상품판이 열립니다. 휴대폰 홈 화면에 추가해 두면 편합니다.

## 4. 첫 실행

**Actions** 탭 › 왼쪽 **상품 수집 (매시간)** › **Run workflow**. 초록색 체크가 뜨면 성공입니다. 이후로는 알아서 돕니다.

링크 만들기: **Actions › 링크 만들기 › Run workflow** 에 쿠팡 주소를 붙여 넣기. 결과는 실행 화면 아래 Summary(와 텔레그램)에 나옵니다. GitHub 휴대폰 앱에서도 됩니다.

## 텔레그램 알림 설정 (선택)

1. 텔레그램에서 `@BotFather` › `/newbot` › 이름 정하기 › 받은 토큰을 `TELEGRAM_BOT_TOKEN` 에
2. 만든 봇에게 아무 메시지나 보내기
3. 브라우저에서 `https://api.telegram.org/bot<토큰>/getUpdates` 열기 › `"chat":{"id": 숫자` 의 숫자를 `TELEGRAM_CHAT_ID` 에

## 알아둘 점

- 실행 시각은 GitHub 사정에 따라 몇 분~수십 분 늦을 수 있습니다.
- 쿠팡 검색 API는 시간당 호출 수 제한이 있어 키워드는 3개까지만 씁니다.
- 실패하면 GitHub가 메일로 알려 줍니다. Actions 실행 기록의 빨간 X를 눌러 오류 문구를 확인하세요.
- 링크를 블로그·SNS에 쓸 때는 "이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다" 문구를 꼭 함께 적어야 합니다.

## 스레드 연결

메타가 화면을 자주 바꿔서 메뉴 이름이 조금 다를 수 있습니다. 막히면 그 화면을 캡처해 Claude에게 보여 주세요.

1. 스레드 계정을 **공개 계정**으로 둡니다.
2. developers.facebook.com 에 로그인 › **내 앱** › **앱 만들기** › 사용 사례에서 **Threads API 액세스** 선택 › 앱 이름 `KINGDOM` 으로 만들기
3. 앱 화면 **사용 사례 › Threads API › 맞춤 설정**에서 권한 `threads_basic`, `threads_content_publish` 추가
4. **설정** 쪽 **Threads 테스터 추가**에서 내 스레드 아이디 등록 › 스레드 앱(또는 웹)의 **설정 › 계정 › 웹사이트 권한 › 초대**에서 수락
5. 앱 화면의 **사용자 토큰 생성기**에서 내 계정 옆 **액세스 토큰 생성** › 나온 토큰을 Secrets 의 `THREADS_ACCESS_TOKEN` 에 저장
6. **Actions › 스레드 자동 게시 › Run workflow** 로 한 번 시험해 보고 스레드에 글이 올라왔는지 확인

### 토큰 자동 갱신 (GH_PAT)

스레드 토큰은 60일이면 만료됩니다. 매주 자동으로 새 토큰을 받아 저장하려면:

1. github.com › 오른쪽 위 프로필 › **Settings › Developer settings › Personal access tokens › Fine-grained tokens › Generate new token**
2. Repository access: **Only select repositories** › `kingdom` 선택
3. Permissions › Repository permissions › **Secrets: Read and write**
4. 만든 토큰을 저장소 Secrets 의 `GH_PAT` 에 저장

## 어떤 상품을 올리나요

파트너스 API 에는 상품별 매출 숫자가 없어서, 아래 순서로 잘 팔리는 상품을 고릅니다.

1. 최근 30일 동안 **내 링크로 실제 주문된 상품**
2. **카테고리 베스트 상위 10위** (쿠팡 판매 인기 순위)
3. 관심 키워드 **검색 상위 5위**
4. 골드박스

같은 상품은 7일 안에 다시 올리지 않습니다. 모든 글 맨 앞에 대가성 문구가 들어갑니다.

## 스레드 운영 주의

- 지금은 4시간마다(하루 6개) 올립니다. 계정 경고가 오면 ``threads.yml`` 의 ``*/4`` 를 ``*/6`` (6시간마다)으로, 더 자주 올리려면 ``*/2`` 로 바꾸세요.
- 대가성 문구는 지우지 마세요. 공정위 지침상 필수입니다.