"""한 번: 유튜브 설명란의 예전(탈퇴한 계정) 쿠팡 링크를 지금 계정의 새 파트너스 링크로 바꿀 표를 만든다.

youtube_links.txt (예전 링크 | 상품 주소 | 상품 이름) → youtube_map.json (예전 링크: 새 링크)
같은 상품 링크가 안 만들어지면(판매 종료 등) 상품 이름으로 쿠팡 검색 링크를 대신 넣는다.
GitHub > Actions > KINGDOM > Run workflow > task 를 youtube-links 로 실행.
유튜브 설명란을 실제로 고치는 건 내 컴퓨터에서 따로 한다 (구글 로그인 필요).
"""
import json
import re
import time
import urllib.parse
from pathlib import Path

import partners as p

ROOT = Path(__file__).parent
SRC = ROOT / "youtube_links.txt"
OUT = ROOT / "youtube_map.json"
FAILED = ROOT / "youtube_failed.json"   # 끝내 새 링크를 못 만든 예전 링크
SEARCH = ROOT / "youtube_search.json"   # 판매 종료 등으로 상품 이름 검색 링크로 대신한 것
BATCH = 20   # 쿠팡 딥링크 API 한 번에 최대 20개


def one(url):
    """URL 하나를 파트너스 짧은 링크로. 안 되면 빈 문자열."""
    try:
        rows = p.deeplink([url])
        return (rows[0].get("shortenUrl") if rows else "") or ""
    except Exception as e:
        print("변환 실패:", url[:80], str(e)[:80])
        return ""
    finally:
        time.sleep(1)


def search_url(name):
    words = re.sub(r"[^0-9A-Za-z가-힣 ]", " ", name).split()[:6]
    return "https://www.coupang.com/np/search?q=" + urllib.parse.quote(" ".join(words)) if words else ""


def main():
    rows = []   # (예전 링크, 상품 주소, 상품 이름)
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "|" in line:
            parts = [s.strip() for s in line.split("|")] + ["", ""]
            if parts[1]:
                rows.append(tuple(parts[:3]))
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}   # 중간에 끊겨도 이어서
    searched = json.loads(SEARCH.read_text(encoding="utf-8")) if SEARCH.exists() else {}

    # 1) 같은 상품 링크: 20개씩 묶어서 (묶음이 거절되면 하나씩)
    targets = sorted({t for o, t, n in rows if o not in done})
    new = {}
    for i in range(0, len(targets), BATCH):
        chunk = targets[i:i + BATCH]
        try:
            got = p.deeplink(chunk)
        except Exception as e:
            print("묶음 실패, 하나씩 다시:", e)
            got = [{"shortenUrl": one(t)} for t in chunk]
        for t, r in zip(chunk, got):   # 쿠팡은 보낸 순서대로 돌려준다
            if r.get("shortenUrl"):
                new[t] = r["shortenUrl"]
        time.sleep(1.5)
    # 2) 옵션 번호(itemId) 없이 상품 번호만으로 다시
    for t in targets:
        if t not in new and "?" in t:
            new[t] = one(t.split("?")[0])
    for o, t, n in rows:
        if o not in done and new.get(t):
            done[o] = new[t]
    # 3) 그래도 안 되면(판매 종료 등) 설명란의 상품 이름으로 쿠팡 검색 링크
    by_name = {}
    for o, t, n in rows:
        if o not in done and n:
            if n not in by_name:
                by_name[n] = one(search_url(n)) if search_url(n) else ""
            if by_name[n]:
                done[o] = by_name[n]
                searched[o] = n

    OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    SEARCH.write_text(json.dumps(searched, ensure_ascii=False, indent=1), encoding="utf-8")
    left = {o: t for o, t, n in rows if o not in done}
    FAILED.write_text(json.dumps(left, ensure_ascii=False, indent=1), encoding="utf-8")
    p.summary(f"## 유튜브 링크 새로 만들기\n\n- 전체 {len(rows)}개 중 완료 {len(done)}개 "
              f"(같은 상품 {len(done) - len(searched)}개, 상품 이름 검색 링크 {len(searched)}개), 못 만듦 {len(left)}개\n")


if __name__ == "__main__":
    main()
