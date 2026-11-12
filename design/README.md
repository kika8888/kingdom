# design — 블로그 꾸미기 이미지와 만드는 프로그램

자동화가 쓰는 파일이 아니다. 블로그 대문·프로필·메뉴 위젯을 다시 만들거나 색만 바꿀 때 쓴다.

## 완성 이미지 (`blog_mk/`)
| 파일 | 어디에 | 크기 |
|---|---|---|
| `stage_1920x600_blue.png` | 블로그 꾸미기 → 스킨배경 → 직접등록 → 상단 영역 (MK 연예계 뉴스 대문) | 1920×600 |
| `profile_600_blue.png` | 관리 → 기본 설정 → 블로그 정보 → 프로필 이미지 (PC 네모, 모바일 동그라미) | 600×600 |
| `menu_170x400_blue.png` | 위젯 직접등록 (코드는 HANDOFF.md 참고, 실제로는 `docs/blogmenu/mk_menu_blue.png` 를 씀) | 170×400 |

## 생활·경제 블로그 "살림 경제 노트" (`blog_economy/`, 청록)
같은 크기·같은 자리: `stage_1920x600_economy.png`(대문), `profile_600_economy.png`(프로필, 그래프+₩ 동전), `menu_170x400_economy.png`(메뉴 위젯: 생활 꿀팁·지원금·정책·재테크·금리·절약·할인).
다시 만들기: `powershell -File make_economy.ps1` (문구·색은 그 파일 안에서 바꾸면 됨)

## 만드는 프로그램 (윈도 PowerShell, 따로 설치할 것 없음)
- `make_stage.ps1` — 기존 연예 블로그(soduwk1209)와 같은 무대 스타일. 대문·메뉴 위젯·프로필을 한 번에.
  색 바꾸기 예: `powershell -File make_stage.ps1 -Name blue -Edge "#06122E" -Mid "#17408A" -T1 "#F4FAFF" -T2 "#9AD4FF" -Glow "#3FA9FF" -Acc "#7FD4FF" -Band "#0A1C40" -Soft "#D6E8FF" -Bokeh "#3FA9FF,#7B6CFF,#FFB86B,#5FE0FF"`
  이름 바꾸기: `-Title "MK 연예계 뉴스"`
- `make_blog_home.ps1`, `make_blog_bg.ps1`, `make_blog_widget.ps1`, `recolor_stage.ps1` — 처음 만든 시안(분홍·보라 그라데이션)용.
- 한글이 들어 있어 **UTF-8 BOM** 으로 저장해야 PowerShell 5.1 에서 돌아간다. 결과는 같은 폴더의 `blog_home\` 아래에 생긴다.

## `test_blog_threads.py`
블로그→스레드 글이 어떻게 만들어지는지 **게시 없이** 미리 보기. 저장소 맨 위에서 `python design/test_blog_threads.py 3` (블로그마다 최근 3개).
