"""한 번: 유튜브 설명란의 예전(탈퇴한 계정) 쿠팡 링크를 지금 계정의 새 파트너스 링크로 바꿀 표를 만든다.

youtube_links.txt (예전 링크 | 상품 주소) → youtube_map.json (예전 링크: 새 링크)
GitHub > Actions > KINGDOM > Run workflow > task 를 youtube-links 로 실행.
유튜브 설명란을 실제로 고치는 건 내 컴퓨터에서 따로 한다 (구글 로그인 필요).
"""
import json
import time
from pathlib import Path

import partners as p

ROOT = Path(__file__).parent
SRC = ROOT / "youtube_links.txt"
OUT = ROOT / "youtube_map.json"
BATCH = 20   # 쿠팡 딥링크 API 한 번에 최대 20개


def main():
    pairs = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "|" in line:
            old, _, target = (s.strip() for s in line.partition("|"))
            if target:
                pairs.append((old, target))
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}   # 중간에 끊겨도 이어서
    targets = sorted({t for o, t in pairs if o not in done})
    new = {}
    failed = []
    for i in range(0, len(targets), BATCH):
        chunk = targets[i:i + BATCH]
        try:
            rows = p.deeplink(chunk)
        except Exception as e:
            failed += chunk
            print("실패:", e)
            time.sleep(5)
            continue
        for t, r in zip(chunk, rows):   # 쿠팡은 보낸 순서대로 돌려준다
            if r.get("shortenUrl"):
                new[t] = r["shortenUrl"]
            else:
                failed.append(t)
        time.sleep(1.5)
    for old, t in pairs:
        if t in new:
            done[old] = new[t]
    OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    p.summary(f"## 유튜브 링크 새로 만들기\n\n- 전체 {len(pairs)}개 중 완료 {len(done)}개, 실패 {len(pairs) - len(done)}개\n"
              + ("- 실패한 상품은 판매 종료일 수 있어요. 다시 실행하면 실패한 것만 다시 시도합니다.\n" if failed else ""))


if __name__ == "__main__":
    main()
