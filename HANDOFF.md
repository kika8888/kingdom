# KINGDOM 이어서 하기 메모 (다른 컴퓨터·새 대화용)

> 집이나 다른 컴퓨터에서 Claude에게: **"github.com/kika8888/kingdom 의 HANDOFF.md 읽고 이어서 해줘"**
> 마지막 업데이트: 2026-10-21

## 사용자
- 비개발자. 한국어로 짧고 쉽게, 한 번에 한 단계씩 안내. 캡처를 보내며 진행.
- 비밀값(토큰·키)은 절대 채팅·코드에 적지 않는다.

## 무엇이 어디 있나
| 것 | 위치 |
|---|---|
| 사이트 | https://kingdom.papalaqi.com (GitHub Pages, 이 저장소 `docs/`) |
| 매시간 수집·페이지 생성 | `collect.py` (끝에 `trends.py`, 실적 백업 보고) |
| 스레드 자동 게시 (@maladubi999, 4시간마다) | `threads.py`, 소재 `picks.txt` (상품이름 \| 첫 줄 문구 \| 영상 \| 검색어) |
| 블로그→스레드 (연예 @yesol276, 스포츠 @pantaqi9988, 매시 47분) | `blog_threads.py` — 글 + 블로그 사진 2장 + 첫 댓글 링크 |
| 자동 영상 | `make_video.py` |
| 카톡 실적 보고 | `report.py` (최근 7일 포함) |
| 워크플로 | `.github/workflows/kingdom.yml` (task: collect, threads, blog, report …) |
| AI 직원 페이지 | `docs/ai/index.html` — 탭: 전체·인턴·MD(상품기획자)·에이스·지원팀·전략팀·영업기획팀, 버튼 "업무 맡기기" |
| 키워드 검색 | `docs/ai/keyword.html` → Cloudflare Worker `https://kingdom-keyword.pantaqi999.workers.dev` (코드 `worker/keyword-worker.js`, 키는 Cloudflare Secrets) |
| 실시간 인기 검색어 | `docs/ai/trends.html` (매시간 `trends.py`) |
| 링크 미리보기 이미지 | `docs/og/*.png` + 각 페이지 `og:` 태그 |
| AI 도구(클로드 아티팩트) | 수익화 모음 https://claude.ai/artifact/JXErbBjjxvVZZTJTGg8YUU#도구id, 스레드&블로그 7mHh5qotz2BZs2hAGaZqCy, 애드센스 SssqzWjuN1upAPd8cHYX5i, 키워드 2nHhx1ejsgFDhuRHj6qBjR, 이미지 6Bc7Db265UTAbCfgcEX7Sv |

휴대폰 화면(640px 이하, `collect.py` PAGE): 네이버 앱처럼 큰 금색 검색창 · 옆으로 넘기는 바로가기 카드(`.mhome`) · 실시간 검색어 한 줄(`/ai/trends.json`) · 아래 고정 메뉴(`.mnav`: 쇼핑·뉴스·AI 직원·키워드·생활찾기). 맨 위 구글 앵커 광고가 화면을 가림 → 끌지는 사용자 결정 대기.

메뉴(맨 위): 쇼핑 · 뉴스 · AI 직원 · 💰 지원금 찾기(index01.pantaqi100.com) · 💊 전국 24시 심야약국(post0020.papalaqi.com) · ⛳ 파크골프장 찾기(pantaqidex14.papalaqi.com)

## 꼭 지킬 규칙
- 아백(aros100) 화면을 캡처해 따라 만들 땐 **도구 구성은 똑같이, 색은 KINGDOM 색(남색 #1e2156~#2e3478 + 금색 #e0b84a)**.
- 이름에 **아백 티 나는 말 금지**: 블로그스팟, 스킨, NEW, 아백, 제자님. 미리보기 등에 "쿠팡" 글자도 빼 달라고 함(단, 페이지의 쿠팡 파트너스 대가성 문구는 법적 필수라 유지).
- 캡처 소재 문구에 **조회수·좋아요 숫자 쓰지 않기**. 가짜 후기·가짜 신분·근거 없는 긴박감 금지.
- 남인 척 댓글, 자동 댓글·공감, 네이버 스크래핑·자동 게시는 하지 않는다(약관 위반).

## 진행 중 / 남은 일
- [ ] 지원금·심야약국·파크골프장(블로그스팟) 테마 `<head>`에 og 태그 붙이기 — 사용자가 직접. 코드는 이미지 `https://kingdom.papalaqi.com/og/support.png`, `pharmacy.png`, `parkgolf.png` 사용.
- [ ] 벤치마킹 글쓰기 도구 — 사용자가 "나중에" (아백 화면 캡처 받으면 다시).
- [ ] 아이디어(사용자 결정 대기): Cloudflare Cron으로 GitHub 예약 실행 깨우기, 매일 아침 S급 키워드 카톡 발굴.
- 조회수·수익 부진(쿠팡 하루 클릭 ~5, 수익 ~1,000원) — 블로그→스레드 사진 방식 바꾼 효과를 지켜보는 중.

## 작업 방법 메모
- 커밋은 GitHub Contents API로(토큰 필요: 회사 PC `C:\Users\부자재창고\kingdom\github_token.txt`. 다른 PC면 새로 발급 — github.com/settings/personal-access-tokens/new, kika8888/kingdom만, Contents·Actions Read and write).
- 실행: `POST /repos/kika8888/kingdom/actions/workflows/kingdom.yml/dispatches` `{ref:"main", inputs:{task:"collect"}}`
