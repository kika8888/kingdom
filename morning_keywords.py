"""☀️ 매일 아침 S급 키워드 발굴: 오늘 실시간 인기 검색어(구글 트렌드)를 씨앗으로
키워드 서버(네이버 검색광고 연관 키워드)를 불러 S급(검색 많고 경쟁 낮음)만 골라 카톡으로 보낸다.

등급 기준은 docs/ai/keyword.html 의 grade() 와 똑같다.
collect.py 가 매시간 부르고, 아침 7시 이후 아직 안 보냈으면 그때 한 번만 보낸다.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import partners as p
import trends

WORKER = "https://kingdom-keyword.pantaqi999.workers.dev/"
PAGE = "https://kingdom.papalaqi.com/ai/keyword.html"
SENT = Path(__file__).parent / "docs" / "keyword_sent.txt"   # 보낸 날짜만 남긴다
COMP = {"낮음": 1, "중간": 2, "높음": 3}


def grade(r):
    t, c = r.get("total") or 0, COMP.get(r.get("adComp"), 2)
    s = (4 if t >= 50000 else 3 if t >= 10000 else 2 if t >= 3000 else 1 if t >= 500 else 0) - (c - 1)
    return "S" if s >= 3 else "A" if s >= 2 else "B" if s >= 1 else "C" if s >= 0 else "D"


def related(kw):
    req = urllib.request.Request(WORKER + "?kw=" + urllib.parse.quote(kw), headers={"User-Agent": "kingdom-bot"})
    with urllib.request.urlopen(req, timeout=40) as res:
        return json.loads(res.read().decode("utf-8")).get("rows") or []


def pick(seeds, n=5):
    """씨앗마다 연관 키워드를 받아 S급만 모은다. 모자라면 A급으로 채운다."""
    found, fails = {}, []
    for seed in seeds:
        try:
            rows = related(seed)
        except Exception as e:
            fails.append(f"{seed}: {e}")
            continue
        for r in rows:
            k = r.get("keyword")
            if k and k not in found:
                found[k] = {**r, "grade": grade(r), "seed": seed}
    if fails:
        print("키워드 조회 실패:", " / ".join(fails)[:500])
    # 문서 수(블로그 글 수)를 알면 검색 대비 글이 적은 순, 모르면 검색 많은 순
    score = lambda r: r["total"] / (r["docs"] + 1) if r.get("docs") else r["total"]
    best = sorted((r for r in found.values() if r["grade"] == "S"), key=score, reverse=True)
    if len(best) < n:
        best += sorted((r for r in found.values() if r["grade"] == "A"), key=score, reverse=True)[:n - len(best)]
    return best[:n], len(found)


def main(once=False):
    now = p.now_kst()
    today = now.strftime("%Y-%m-%d")
    if once or "--once" in sys.argv:
        if now.hour < 7:
            print("아침 7시 전이라 키워드 알림은 나중에 보냅니다.")
            return
        if SENT.exists() and SENT.read_text(encoding="utf-8").strip() == today:
            print("오늘 키워드 알림은 이미 보냈습니다.")
            return

    items = trends.fetch()
    # 사건·사고 키워드는 글감으로 위험해 빼고, 키워드 서버가 받는 40자 이하만 위에서부터 10개
    seeds = [it["kw"] for it in items if len(it["kw"]) <= 40
             and not any(w in " ".join(n["title"] for n in it["news"]) for w in trends.CAUTION)][:10]
    if not seeds:
        raise SystemExit("씨앗 키워드(실시간 검색어)를 못 가져왔어요")
    best, total = pick(seeds)
    if not best:
        raise SystemExit(f"연관 키워드 {total}개 중 S·A급이 없거나 키워드 서버가 응답하지 않았어요")

    lines = [f"{r['grade']} {r['keyword']} {r['total']:,}" for r in best]
    errors = p.notify(f"☀️ {now.strftime('%m.%d')} 오늘의 S급 키워드\n(키워드 / 월 검색수)\n" + "\n".join(lines),
                      link=PAGE, button="키워드 더 보기")
    p.summary(f"## {today} 아침 키워드\n\n씨앗: {', '.join(seeds)}\n\n연관 {total}개 중\n\n"
              "| 등급 | 키워드 | 월 검색 | 경쟁 | 씨앗 |\n|---|---|---:|---|---|\n"
              + "".join(f"| {r['grade']} | {r['keyword']} | {r['total']:,} | {r['adComp']} | {r['seed']} |\n" for r in best))
    if errors:
        raise SystemExit("키워드 알림을 보내지 못했습니다: " + " / ".join(errors))
    SENT.parent.mkdir(exist_ok=True)
    SENT.write_text(today, encoding="utf-8")


if __name__ == "__main__":
    main()
