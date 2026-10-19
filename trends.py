"""📡 실시간 키워드 전략팀: 구글 트렌드(한국) 실시간 인기 검색어 TOP 10 을 매시간 모아
키워드마다 '어떤 직원이 어떤 방향으로 쓰면 좋은지' 전략을 붙여 docs/ai/trends.html 로 만든다.

collect.py 가 매시간 수집 끝에 부른다. 실패해도 쇼핑 수집에는 영향이 없다.
전략은 키워드·뉴스 제목의 단어로 분류하는 규칙이라 AI 가 아니다. 사건·인물 키워드는 주의 표시를 붙인다.
"""
import email.utils
import html
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta, timezone
from pathlib import Path

RSS = "https://trends.google.com/trending/rss?geo=KR"
HT = "{https://trends.google.com/trending/rss}"
OUT = Path(__file__).parent / "docs" / "ai"
KST = timezone(timedelta(hours=9))

TOOLS = "https://claude.ai/artifact/JXErbBjjxvVZZTJTGg8YUU"
# (분류, 추천 직원, 맡길 도구 주소, 글 방향, 제목 틀 2개, 판별 단어)
CATS = [
    ("support", "💰 지원금 직원", TOOLS + "#support", "대상·금액·신청 방법을 공식 안내 기준으로 정리",
     ["{k} 신청 방법·대상 총정리 (공식 안내 기준)", "{k} 받을 수 있는 사람? 조건 한눈에"],
     ["지원금", "신청", "지급", "바우처", "수당", "장려금", "청약", "대출", "연금", "환급", "보조금", "정책", "세금", "공공요금", "배송비"]),
    ("money", "📈 에이스 · 글쓰기 직원", "https://claude.ai/artifact/MxzCDB5Tx9jXAxoLRyA9pv#blog", "무슨 일인지 쉽게 풀고 내 돈에 미치는 영향 정리",
     ["{k} 왜 이렇게 움직였을까? 오늘 이슈 정리", "{k} 뉴스 쉽게 정리, 알아둘 점 3가지"],
     ["코스피", "코스닥", "주식", "증권", "금리", "환율", "비트코인", "코인", "증시", "ETF", "거래소", "배당", "부동산", "아파트"]),
    ("shop", "🛒 MD (상품기획자)", "https://claude.ai/artifact/7mHh5qotz2BZs2hAGaZqCy", "가격·특징 비교, 쿠팡에서 살 수 있는 비슷한 상품 소개",
     ["{k} 요즘 왜 화제? 가격·특징 한눈에", "{k} 대신 쿠팡에서 찾은 비슷한 상품"],
     ["다이소", "쿠팡", "올리브영", "이마트", "홈플러스", "편의점", "파리바게뜨", "스타벅스", "맥도날드", "할인", "출시", "신상", "품절", "택배", "세일", "아이폰", "갤럭시"]),
    ("sports", "⚽ 스포츠 블로그", "https://claude.ai/artifact/7mHh5qotz2BZs2hAGaZqCy", "경기 결과·선수 소식을 확인된 내용만 요약",
     ["{k} 경기·소식 한눈에 정리", "{k} 화제인 이유 3줄 요약"],
     ["감독", "야구", "축구", "골프", "골퍼", "선수", "리그", "대표팀", "농구", "배구", "올림픽", "월드컵", "KBO", "MLB", "우승", "경기"]),
    ("ent", "🎤 연예 블로그", "https://claude.ai/artifact/7mHh5qotz2BZs2hAGaZqCy", "근황·방송 소식을 확인된 내용만 정리 (루머 금지)",
     ["{k} 근황, 화제가 된 이유 정리", "{k} 관련 소식 한눈에 (확인된 내용만)"],
     ["드라마", "배우", "가수", "아이돌", "예능", "컴백", "결혼", "열애", "방송", "편성", "콘서트", "영화", "넷플릭스", "시청률"]),
]
DEFAULT = ("issue", "✍️ 에이스 · 글쓰기 직원", "https://claude.ai/artifact/MxzCDB5Tx9jXAxoLRyA9pv#blog", "무슨 일인지 핵심만 정리",
           ["{k} 무슨 일? 핵심만 3줄 정리", "{k} 화제인 이유와 알아둘 점"], [])
CAUTION = ["명예훼손", "구속", "사망", "숨진", "피의자", "혐의", "논란", "폭행", "성범죄", "사고", "고소", "재판", "체포", "참사"]


def fetch():
    req = urllib.request.Request(RSS, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        root = ET.fromstring(res.read())
    out = []
    for it in root.iter("item"):
        kw = (it.findtext("title") or "").strip()
        if not kw:
            continue
        news = [{"title": (n.findtext(f"{HT}news_item_title") or "").strip(),
                 "url": (n.findtext(f"{HT}news_item_url") or "").strip(),
                 "source": (n.findtext(f"{HT}news_item_source") or "").strip()} for n in it.iter(f"{HT}news_item")]
        try:
            t = email.utils.parsedate_to_datetime(it.findtext("pubDate") or "").astimezone(KST)
            when = t.strftime("%m월 %d일 %H:%M")
        except (TypeError, ValueError):
            when = ""
        out.append({"kw": kw, "traffic": (it.findtext(f"{HT}approx_traffic") or "").strip(), "when": when,
                    "news": [n for n in news if n["title"]][:2]})
    return out


def classify(item):
    """키워드 자체로 먼저 판단하고(코스피 → 금융), 없으면 뉴스 제목에서 가장 많이 걸린 분류."""
    kw = item["kw"].lower()
    for cat in CATS:
        if any(w.lower() in kw for w in cat[5]):
            return cat
    text = " ".join(n["title"] for n in item["news"]).lower()
    hits = [(sum(text.count(w.lower()) for w in cat[5]), -n, cat) for n, cat in enumerate(CATS)]
    best = max(hits, key=lambda h: (h[0], h[1]))
    return best[2] if best[0] else DEFAULT


def card(i, item):
    key, who, tool, angle, titles, _ = classify(item)
    k = item["kw"]
    e = lambda s: html.escape(str(s), quote=True)
    hot = item["traffic"].replace("+", "").replace(",", "")
    hot = int(hot) if hot.isdigit() else 0
    caution = any(w in " ".join(n["title"] for n in item["news"]) for w in CAUTION)
    news = "".join(f'<li><a href="{e(n["url"])}" target="_blank" rel="noopener">{e(n["title"])}</a>'
                   f'{f" <small>· {e(n["source"])}</small>" if n["source"] else ""}</li>' for n in item["news"])
    return (f'<article class="tc" data-k="{e(key)}"><div class="top"><span class="rk">{i}</span>'
            f'<div class="kw"><h2>{e(k)}</h2><span class="meta">{"🔥 " if hot >= 1000 else ""}검색 {e(item["traffic"] or "-")}'
            f'{f" · {e(item["when"])}" if item["when"] else ""}</span></div><span class="who">{e(who)}</span></div>'
            + (f'<ul class="news">{news}</ul>' if news else "")
            + f'<div class="plan"><b>📋 전략</b> {e(angle)}<ol>' + "".join(f"<li>{e(t.format(k=k))}</li>" for t in titles) + "</ol></div>"
            + ('<p class="warn">⚠️ 사건·인물 키워드예요. 확인된 사실만 쓰고 추측·비방은 하지 마세요.</p>' if caution else "")
            + f'<div class="btns"><button type="button" class="b copy" data-t="{e(k)}">키워드 복사</button>'
            f'<a class="b go" href="{e(tool)}" target="_blank" rel="noopener">추천 직원에게 맡기기 →</a>'
            f'<a class="b" href="https://search.naver.com/search.naver?query={urllib.parse.quote(k)}" target="_blank" rel="noopener">네이버에서 보기</a></div></article>')


PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KINGDOM 실시간 키워드 전략팀</title><meta name="description" content="지금 한국에서 가장 많이 찾는 검색어 TOP 10과 글쓰기 전략">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap">
<style>
:root{--navy:#1e2156;--navy2:#2e3478;--gold:#e0b84a;--ink:#17182b;--muted:#5d6072;--line:#e6e4ee;--bg:#f6f5f1}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Noto Sans KR","Malgun Gothic",sans-serif}
header{background:var(--navy);color:#fff}header .in{max-width:1100px;margin:0 auto;padding:12px 16px;display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.brand{font-weight:900;letter-spacing:.06em;color:#fff;text-decoration:none}.brand b{color:var(--gold)}nav a{color:#cfd2ee;text-decoration:none;margin-right:16px;font-weight:500}nav a.on{color:var(--gold)}
main{max-width:1100px;margin:0 auto;padding:22px 16px 50px}
.hero{text-align:center;padding:10px 0 18px}.hero h1{margin:0;font-size:1.6rem;font-weight:900;color:var(--navy)}.hero p{margin:6px 0 0;color:var(--muted)}
.upd{display:inline-block;margin-top:10px;background:#fff;border:1px solid #ecd28a;border-radius:999px;padding:4px 14px;font-size:.84rem}
.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
.tc{background:#fff;border:1px solid var(--line);border-top:4px solid var(--navy2);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px}
.tc[data-k=support]{border-top-color:#0f7a5a}.tc[data-k=shop]{border-top-color:#b4234a}.tc[data-k=money]{border-top-color:#c9971f}.tc[data-k=sports]{border-top-color:#1d4ed8}.tc[data-k=ent]{border-top-color:#9333ea}
.top{display:flex;gap:10px;align-items:flex-start}.rk{flex:none;width:32px;height:32px;border-radius:50%;background:var(--navy);color:var(--gold);font-weight:900;display:flex;align-items:center;justify-content:center}
.kw{flex:1;min-width:0}.kw h2{margin:0;font-size:1.15rem;line-height:1.3;word-break:keep-all}.meta{font-size:.78rem;color:var(--muted)}
.who{flex:none;font-size:.74rem;font-weight:700;background:#fdf3d4;color:#7a5a08;border-radius:999px;padding:3px 9px;white-space:nowrap}
.news{margin:0;padding-left:18px;font-size:.84rem}.news a{color:var(--ink)}.news small{color:var(--muted)}
.plan{background:#f8f7fc;border-radius:10px;padding:10px 12px;font-size:.86rem}.plan ol{margin:6px 0 0;padding-left:20px}
.warn{margin:0;background:#fff4f4;color:#9f1239;border-radius:8px;padding:8px 10px;font-size:.8rem}
.btns{display:flex;gap:6px;flex-wrap:wrap}.b{font:inherit;font-size:.8rem;font-weight:700;border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:8px;padding:7px 10px;cursor:pointer;text-decoration:none}
.b.go{background:var(--navy);color:#fff;border-color:var(--navy)}.b:focus-visible{outline:3px solid var(--gold)}
.note{margin-top:18px;font-size:.8rem;color:var(--muted);text-align:center}
</style></head><body>
<header><div class="in"><a class="brand" href="/">👑 <b>KINGDOM</b></a><nav><a href="/">쇼핑</a><a href="/#car">뉴스</a><a href="/ai" class="on">AI 직원</a></nav></div></header>
<main><section class="hero"><h1>📡 실시간 키워드 전략팀</h1><p>지금 한국에서 가장 많이 찾는 검색어 TOP 10과, 어떤 직원이 어떻게 쓰면 좋은지 전략을 매시간 정리해요</p>
<span class="upd">🕒 마지막 갱신 {updated} · 출처: Google 트렌드(대한민국)</span></section>
<div class="list">{cards}</div>
<p class="note">검색량은 구글 트렌드 추정치예요. 전략은 키워드 분류에 따른 추천이니 글을 쓰기 전에 뉴스로 사실을 꼭 확인하세요. <a href="/ai">← AI 직원 목록</a></p></main>
<script>document.addEventListener('click',async e=>{const b=e.target.closest('.copy');if(!b)return;try{await navigator.clipboard.writeText(b.dataset.t);b.textContent='복사됨 ✓'}catch(x){prompt('복사하세요',b.dataset.t)}setTimeout(()=>b.textContent='키워드 복사',1500)});</script>
</body></html>"""


def main(now_text=""):
    items = fetch()
    if not items:
        raise RuntimeError("구글 트렌드에서 키워드를 못 가져왔어요")
    OUT.mkdir(parents=True, exist_ok=True)
    cards = "".join(card(i + 1, it) for i, it in enumerate(items[:10]))
    (OUT / "trends.html").write_text(PAGE.replace("{updated}", now_text).replace("{cards}", cards), encoding="utf-8")
    (OUT / "trends.json").write_text(json.dumps({"updated": now_text, "items": items[:10]}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    return len(items)


if __name__ == "__main__":
    from datetime import datetime
    print(main(datetime.now(KST).strftime("%Y-%m-%d %H:%M")))
