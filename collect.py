"""매시간: 골드박스 + 관심 키워드 상품을 모아 docs/ 웹페이지를 새로 만든다.

docs/index.html 은 GitHub Pages 로 휴대폰에서 열 수 있다.
상품 링크는 쿠팡 API 가 내 파트너스 추적 링크로 돌려준 주소 그대로다.

관심 키워드: 저장소 Settings > Secrets and variables > Actions > Variables 에
SEARCH_KEYWORDS 를 "캠핑의자, 무선청소기" 처럼 쉼표로 넣는다.
쿠팡 검색 API 는 시간당 호출 수가 제한돼 있어 한 번에 3개까지만 쓴다.
"""
import html
import json
import os
from pathlib import Path

import partners as p

OUT = Path(__file__).parent / "docs"
MAX_KEYWORDS = 3
# SEARCH_KEYWORDS 를 비워 두면 쓰는 희귀템(신기템) 키워드. 매시간 3개씩 돌아가며 검색한다.
WEIRD_KEYWORDS = ["신기한 아이디어 상품", "차량용 신기템", "주방 아이디어 용품", "자취 꿀템", "캠핑 신기템",
                  "욕실 정리 아이디어", "청소 꿀템", "반려동물 신기템", "책상 정리 아이디어", "다이소 대체 꿀템",
                  "냉장고 정리 아이디어", "육아 아이디어 용품", "낚시 신기템", "세탁 꿀템", "수납 아이디어"]


def won(v):
    try:
        return f"{int(float(v)):,}원"
    except (TypeError, ValueError):
        return ""


def card(item):
    e = lambda k: html.escape(str(item.get(k) or ""), quote=True)
    badges = []
    if item.get("isRocket"):
        badges.append('<span class="b">로켓</span>')
    if item.get("isFreeShipping"):
        badges.append('<span class="b">무료배송</span>')
    rate = item.get("discountRate")
    if rate:
        badges.append(f'<span class="b sale">{html.escape(str(rate))}%</span>')
    return f"""<li class="card">
  <img src="{e('productImage')}" alt="" loading="lazy" width="230" height="230">
  <div class="info">
    <a class="name" href="{e('productUrl')}" target="_blank" rel="noopener sponsored">{e('productName')}</a>
    <div class="price">{won(item.get('productPrice'))}</div>
    <div class="badges">{''.join(badges)}</div>
    <button type="button" data-link="{e('productUrl')}" data-name="{e('productName')}">문구+링크 복사</button>
  </div>
</li>"""


def section(title, items):
    if not items:
        return ""
    return (f'<section><h2>{html.escape(title)} <small>{len(items)}개</small></h2>'
            f'<ul class="grid">{"".join(card(i) for i in items)}</ul></section>')


PAGE = """<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>KINGDOM</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--muted:#5f6673;--line:#e3e6eb;--accent:#c4302b;--chip:#eef0f3}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--card:#1b1e23;--ink:#eceef2;--muted:#9aa1ad;--line:#2b2f36;--accent:#ff6b62;--chip:#262a31;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;padding:0 16px}
.wrap{max-width:1100px;margin:0 auto;padding-block:28px 60px}
header{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;margin-bottom:8px}
h1{font-size:1.5rem;margin:0}.upd{color:var(--muted);font-size:.9rem}
.notice{font-size:.85rem;color:var(--muted);background:var(--chip);padding:10px 12px;border-radius:8px;margin:12px 0 24px}
h2{font-size:1.15rem;margin:28px 0 12px}h2 small{color:var(--muted);font-weight:400;font-size:.85rem}
.grid{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;height:auto;aspect-ratio:1;object-fit:cover;background:var(--chip)}
.info{padding:10px;display:flex;flex-direction:column;gap:6px;flex:1;min-width:0}
.name{color:var(--ink);text-decoration:none;font-size:.88rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.price{font-weight:700}.badges{display:flex;flex-wrap:wrap;gap:4px;min-height:20px}
.b{font-size:.72rem;background:var(--chip);color:var(--muted);padding:1px 6px;border-radius:4px}.b.sale{color:var(--accent)}
button{margin-top:auto;border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:6px;padding:7px;font:inherit;font-size:.85rem;cursor:pointer}
button:hover,button:focus-visible{border-color:var(--accent);outline:none}
.empty{color:var(--muted)}
</style></head><body><div class="wrap">
<header><h1>KINGDOM</h1><span class="upd">마지막 갱신 {updated} (매시간 자동)</span></header>
<p class="notice">이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. '문구+링크 복사' 버튼을 누르면 이 문구가 링크와 함께 복사됩니다.</p>
{sections}
</div>
<script>
document.addEventListener('click',function(e){var b=e.target.closest('button[data-link]');if(!b)return;
var t=b.textContent;function done(m){b.textContent=m;setTimeout(function(){b.textContent=t},1500)}
var txt='이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\\n\\n'+b.dataset.name+'\\n'+b.dataset.link;
navigator.clipboard.writeText(txt).then(function(){done('복사됨')},function(){prompt('아래 내용을 복사하세요',txt)})});
</script></body></html>"""


def main():
    OUT.mkdir(exist_ok=True)
    data = {"updated": p.now_kst().strftime("%Y-%m-%d %H:%M"), "goldbox": [], "keywords": {}, "best": {}}
    errors = []

    try:
        data["goldbox"] = p.goldbox()
    except Exception as e:
        errors.append(f"골드박스: {e}")

    # 카테고리 베스트: 쿠팡 판매 인기 순위. BEST_CATEGORIES 변수로 고를 수 있고 없으면 전체.
    wanted = [c.strip() for c in os.environ.get("BEST_CATEGORIES", "").split(",") if c.strip()]
    cats = wanted or list(p.BEST_CATEGORIES)
    data["best"] = {}
    for cid in cats:
        name = p.BEST_CATEGORIES.get(cid, cid)
        try:
            data["best"][name] = p.best(cid)
        except Exception as e:
            errors.append(f"베스트 '{name}': {e}")

    keywords = [k.strip() for k in os.environ.get("SEARCH_KEYWORDS", "").split(",") if k.strip()] or WEIRD_KEYWORDS
    start = (p.now_kst().hour * MAX_KEYWORDS) % len(keywords)   # 시간마다 다른 키워드 3개
    for kw in (keywords * 2)[start:start + min(MAX_KEYWORDS, len(keywords))]:
        try:
            data["keywords"][kw] = p.search(kw)
        except Exception as e:
            errors.append(f"검색 '{kw}': {e}")

    sections = section("오늘의 골드박스", data["goldbox"])
    for kw, items in data["keywords"].items():
        sections += section(f"‘{kw}’ 검색 상위", items)
    for name, items in data["best"].items():
        sections += section(f"{name} 베스트", items[:10])
    if not sections:
        sections = '<p class="empty">아직 모은 상품이 없습니다. Actions 실행 기록을 확인해 주세요.</p>'

    (OUT / "index.html").write_text(PAGE.replace("{updated}", data["updated"]).replace("{sections}", sections),
                                    encoding="utf-8")
    (OUT / "products.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    p.summary(f"## 수집 완료 {data['updated']}\n\n- 골드박스 {len(data['goldbox'])}개\n" +
              "".join(f"- '{k}' {len(v)}개\n" for k, v in data["keywords"].items()) +
              f"- 카테고리 베스트 {sum(len(v) for v in data['best'].values())}개\n")
    if errors:
        p.summary("### 실패\n" + "\n".join(f"- {x}" for x in errors))
        if not data["goldbox"] and not data["keywords"] and not data["best"]:
            raise SystemExit("모든 수집이 실패했습니다. API 키를 확인해 주세요.")


if __name__ == "__main__":
    main()
