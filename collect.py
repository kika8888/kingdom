"""매시간: 골드박스 + 관심 키워드 상품을 모아 docs/ 웹페이지를 새로 만든다.

docs/index.html 은 GitHub Pages 로 휴대폰에서 열 수 있다.
상품 링크는 쿠팡 API 가 내 파트너스 추적 링크로 돌려준 주소 그대로다.

관심 키워드: 저장소 Settings > Secrets and variables > Actions > Variables 에
SEARCH_KEYWORDS 를 "캠핑의자, 무선청소기" 처럼 쉼표로 넣는다.
쿠팡 검색 API 는 시간당 호출 수가 제한돼 있어 한 번에 3개까지만 쓴다.
"""
import email.utils
import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
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


NAVER_BLOG_ID = os.environ.get("NAVER_BLOG_ID", "").strip() or "soduwk1209"      # 연예계 뉴스
SPORTS_BLOG_ID = os.environ.get("SPORTS_BLOG_ID", "").strip() or "dkdk521"      # 스포츠 뉴스
CAR_BLOG_ID = os.environ.get("CAR_BLOG_ID", "").strip() or "tikitaka_9"      # 자동차 뉴스


def parse_rss(xml_bytes, n=6):
    """네이버 블로그 RSS 에서 제목·요약·대표 사진·날짜만 뽑는다. 글 전체는 옮기지 않는다(중복 문서 방지)."""
    root = ET.fromstring(xml_bytes)
    posts = []
    for it in root.iter("item"):
        desc = it.findtext("description") or ""
        img = re.search(r'<img[^>]+src="([^"]+)"', desc)
        text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", desc))).strip()
        try:
            d = email.utils.parsedate_to_datetime(it.findtext("pubDate") or "")
            date = f"{d.month}월 {d.day}일"
        except (TypeError, ValueError):
            date = ""
        posts.append({
            "title": (it.findtext("title") or "").strip(),
            "link": (it.findtext("link") or "").split("?")[0],
            "summary": text[:90],
            "image": img.group(1) if img else "",
            "date": date,
        })
        if len(posts) >= n:
            break
    return posts


def naver_posts(blog_id=NAVER_BLOG_ID):
    req = urllib.request.Request(f"https://rss.blog.naver.com/{blog_id}.xml",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return parse_rss(res.read())


def post_card(post):
    e = lambda k: html.escape(str(post.get(k) or ""), quote=True)
    img = (f'<img src="{e("image")}" alt="" loading="lazy" width="512" height="512" referrerpolicy="no-referrer">'
           if post.get("image") else "")
    return f"""<li class="card post" data-name="{e('title').lower()}">
  <a class="thumb" href="{e('link')}" target="_blank" rel="noopener">{img}</a>
  <div class="info">
    <a class="name" href="{e('link')}" target="_blank" rel="noopener">{e('title')}</a>
    <p class="sum">{e('summary')}</p>
    <div class="badges"><span class="b">{e('date')}</span></div>
    <a class="buy more" href="{e('link')}" target="_blank" rel="noopener">기사 보기</a>
  </div>
</li>"""


def card(item, tag=""):
    e = lambda k: html.escape(str(item.get(k) or ""), quote=True)
    url = e("productUrl")
    rel = 'target="_blank" rel="sponsored nofollow noopener"'
    badges = []
    if item.get("isRocket"):
        badges.append('<span class="b rocket">로켓배송</span>')
    if item.get("isFreeShipping"):
        badges.append('<span class="b">무료배송</span>')
    rate = item.get("discountRate")
    rate_html = f'<b class="rate">{html.escape(str(rate))}%</b>' if rate else ""
    orig = item.get("originalPrice")
    orig_html = f'<s>{won(orig)}</s>' if orig and str(orig) != str(item.get("productPrice")) else ""
    tag_html = f'<span class="tag">{html.escape(tag)}</span>' if tag else ""
    return f"""<li class="card" data-name="{e('productName').lower()}">
  <a class="thumb" href="{url}" {rel}><img src="{e('productImage')}" alt="" loading="lazy" width="512" height="512">{tag_html}</a>
  <div class="info">
    <a class="name" href="{url}" {rel}>{e('productName')}</a>
    <div class="price">{rate_html}<span>{won(item.get('productPrice'))}</span>{orig_html}</div>
    <div class="badges">{''.join(badges)}</div>
    <a class="buy" href="{url}" {rel}>구매하기</a>
    <button type="button" class="admin-only" data-link="{url}" data-name="{e('productName')}">문구+링크 복사</button>
  </div>
</li>"""


def section(title, items, group, sid, tagger=None):
    if not items:
        return ""
    cards = "".join(card(i, tagger(i) if tagger else "") for i in items)
    return (f'<section class="sec" data-group="{group}" id="{sid}"><h2>{html.escape(title)} <small>{len(items)}개</small></h2>'
            f'<ul class="grid">{cards}</ul></section>')


def rank_tag(item):
    r = item.get("rank")
    return f"BEST {r}" if r else ""


CROWN = ('<svg viewBox="0 0 32 24" width="34" height="26" aria-hidden="true"><path fill="currentColor" '
         'd="M2 6l7 6 7-10 7 10 7-6-3 16H5z"/><rect x="5" y="21" width="22" height="3" rx="1" fill="currentColor"/></svg>')

PAGE = """<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>KINGDOM · 오늘의 신기템 & 특가</title>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3166823959561954" crossorigin="anonymous"></script>
<meta name="description" content="쿠팡에서 지금 뜨는 신기템, 골드박스 특가, 분야별 베스트를 매시간 모아 보여 드려요.">
<style>
:root{--bg:#f5f4f0;--card:#fff;--ink:#17182b;--muted:#5d6072;--line:#e4e2da;--navy:#1c1f4a;--gold:#c9a227;--gold-ink:#7a5f0c;--sale:#d1342b;--rocket:#1b6fd6;--chip:#ecebe5}
@media (prefers-color-scheme:dark){:root{--bg:#111225;--card:#1a1c33;--ink:#ecebf5;--muted:#a3a5bb;--line:#2b2d4a;--navy:#0b0c1d;--gold:#e0bb45;--gold-ink:#e0bb45;--sale:#ff6a5f;--rocket:#6aa8ff;--chip:#24264a;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif}
a{color:inherit}
.top{background:var(--navy);color:#fff;padding:22px 16px 18px}
.top .in{max-width:1120px;margin:0 auto;display:flex;flex-direction:column;gap:6px}
.brand{display:flex;align-items:center;gap:10px;color:var(--gold)}
.brand b{font-size:1.7rem;letter-spacing:.18em;color:#fff}
.tagline{color:#c9cbe0;font-size:.95rem;margin:0}
.notice{background:#2a2d5e;color:#e3e4f2;font-size:.8rem;padding:8px 16px;text-align:center}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px}
.bar .in{max-width:1120px;margin:0 auto;display:flex;flex-direction:column;gap:10px}
.tabs,.chips{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none}
.tabs button,.chips a{flex:none;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:7px 14px;font:inherit;font-size:.9rem;cursor:pointer;text-decoration:none}
.tabs button[aria-pressed="true"]{background:var(--navy);color:#fff;border-color:var(--navy)}
.chips{display:none}.chips.show{display:flex}.chips a{font-size:.8rem;padding:5px 11px}
#q{width:100%;padding:10px 14px;border:1px solid var(--line);border-radius:10px;font:inherit;background:var(--card);color:var(--ink)}
main{max-width:1120px;margin:0 auto;padding:8px 16px 60px}
h2{font-size:1.15rem;margin:30px 0 12px;scroll-margin-top:140px}h2 small{color:var(--muted);font-weight:400;font-size:.85rem}
.grid{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.thumb{position:relative;display:block;background:var(--chip)}
.thumb img{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:cover}
.tag{position:absolute;left:8px;top:8px;background:var(--gold);color:#1c1f4a;font-size:.72rem;font-weight:800;padding:2px 7px;border-radius:6px}
.info{padding:10px;display:flex;flex-direction:column;gap:6px;flex:1;min-width:0}
.name{text-decoration:none;font-size:.88rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}
.price{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px;font-weight:800;font-size:1.05rem}
.price .rate{color:var(--sale)}.price s{color:var(--muted);font-weight:400;font-size:.8rem}
.badges{display:flex;flex-wrap:wrap;gap:4px;min-height:20px}
.b{font-size:.72rem;background:var(--chip);color:var(--muted);padding:1px 6px;border-radius:4px}.b.rocket{color:var(--rocket);font-weight:700}
.buy{margin-top:auto;display:block;text-align:center;background:var(--sale);color:#fff;text-decoration:none;font-weight:800;border-radius:8px;padding:9px 6px;font-size:.88rem}
.buy:hover,.buy:focus-visible{filter:brightness(1.08);outline:2px solid var(--gold);outline-offset:1px}
.admin-only{display:none;border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:6px;padding:6px;font:inherit;font-size:.8rem;cursor:pointer}
body.admin .admin-only{display:block}
.empty{color:var(--muted);text-align:center;padding:40px 0}
.sum{margin:0;font-size:.8rem;color:var(--muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.buy.more{background:var(--navy)}
.about{max-width:1120px;margin:0 auto;padding:10px 16px 20px;color:var(--ink)}.about p,.about li{max-width:70ch;color:var(--muted)}.about ul{padding-left:1.2em}
.cpsearch{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:4px 14px 10px;margin-top:18px}.cpsearch h2{margin:12px 0 8px}.cpsearch iframe{display:block;max-width:100%}
footer{max-width:1120px;margin:0 auto;padding:24px 16px 40px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line)}
@media (max-width:640px){
.top{padding:12px 16px 10px}.brand svg{width:24px;height:18px}.brand b{font-size:1.15rem;letter-spacing:.14em}.tagline{display:none}
.notice{font-size:.68rem;padding:5px 14px}
.bar{padding:8px 12px}.bar .in{gap:8px}
#q{border-radius:999px;padding:11px 18px;box-shadow:0 2px 10px rgba(28,31,74,.08);border-color:transparent;font-size:.9rem}
.tabs button,.chips a{padding:5px 12px;font-size:.8rem}
main{padding:4px 0 40px}
.cpsearch{margin:10px 12px 0;padding:2px 10px 6px;border-radius:16px}.cpsearch h2{font-size:.95rem;margin:10px 0 4px}.cpsearch h2 small{display:none}
.sec h2{font-size:1rem;margin:22px 16px 10px}
.grid{display:flex;overflow-x:auto;gap:10px;padding:0 16px 6px;scroll-snap-type:x mandatory;scrollbar-width:none}
.grid::-webkit-scrollbar{display:none}
.card{flex:0 0 40%;max-width:160px;scroll-snap-align:start;border-radius:14px;border:0;box-shadow:0 1px 6px rgba(28,31,74,.08)}
.info{padding:8px;gap:4px}.name{font-size:.78rem;min-height:2.5em}.price{font-size:.92rem;gap:4px}.price s{font-size:.7rem}
.b{font-size:.65rem}.badges{min-height:16px}.tag{font-size:.62rem;left:6px;top:6px}
.buy{padding:6px 4px;font-size:.76rem;border-radius:999px}.sum{font-size:.72rem}
.about{padding:6px 16px 12px;font-size:.85rem}.about h2{font-size:1rem}
footer{font-size:.72rem;padding:16px 16px 30px}
}
</style></head><body>
<div class="top"><div class="in">
<div class="brand">CROWN<b>KINGDOM</b></div>
<p class="tagline">쿠팡에서 지금 뜨는 신기템 · 골드박스 특가 · 분야별 베스트를 매시간 모아요</p>
</div></div>
<div class="notice">이 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</div>
<div class="bar"><div class="in">
<input id="q" type="search" placeholder="상품 이름으로 찾기 (예: 수납, 차량, 물티슈)" autocomplete="off">
<div class="tabs" role="group" aria-label="보기">
<button type="button" data-g="all" aria-pressed="true">전체</button>
<button type="button" data-g="weird" aria-pressed="false">🔥 신기템</button>
<button type="button" data-g="goldbox" aria-pressed="false">⏰ 골드박스</button>
<button type="button" data-g="best" aria-pressed="false">🏆 분야별 베스트</button>
<button type="button" data-g="car" aria-pressed="false">🚗 자동차</button>
<button type="button" data-g="sports" aria-pressed="false">⚽ 스포츠</button>
<button type="button" data-g="blog" aria-pressed="false">📰 연예 뉴스</button>
</div>
<div class="chips" id="chips">{chips}</div>
</div></div>
<main>
<section class="cpsearch"><h2>🔎 쿠팡 전체에서 찾기 <small>원하는 상품이 위에 없으면 여기서 검색하세요</small></h2>
<iframe title="쿠팡 상품 검색" src="https://coupa.ng/cp0DM8" width="100%" height="75" frameborder="0" scrolling="no" referrerpolicy="unsafe-url"></iframe>
</section>
{sections}
<p class="empty" id="none" hidden>KINGDOM 추천 상품에는 없어요. 위의 '🔎 쿠팡 전체에서 찾기'에서 검색해 보세요.</p>
</main>
<section class="about"><h2>KINGDOM은 이런 곳이에요</h2>
<p>쿠팡에 올라오는 수많은 상품 중 <b>“이런 게 있었어?”</b> 싶은 아이디어 상품과 그날의 특가를 골라 한곳에 모아 둔 페이지예요. 매시간 쿠팡 파트너스 정보를 받아 자동으로 새로 고쳐요.</p>
<ul><li><b>🔥 신기템</b>: 수납·청소·차량·캠핑처럼 생활을 편하게 해 주는 아이디어 상품을 주제별로 모았어요.</li>
<li><b>⏰ 골드박스</b>: 쿠팡이 하루 동안만 할인하는 특가 상품이에요. 다음 날이면 바뀌어요.</li>
<li><b>🏆 분야별 베스트</b>: 쿠팡 분야별 판매 인기 순위 상위 상품이에요.</li></ul>
<p>가격과 할인, 배송 조건은 쿠팡에서 수시로 바뀌니 구매 전에 쿠팡 화면에서 꼭 확인해 주세요.</p></section>
<footer>마지막 갱신 {updated} · 매시간 자동 업데이트<br>가격, 할인, 배송 조건은 쿠팡에서 바뀔 수 있으니 구매 전에 쿠팡 화면에서 확인해 주세요.<br>이 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</footer>
<script>
(function(){
if(location.hash==='#admin')document.body.classList.add('admin');
var g='all',q=document.getElementById('q'),chips=document.getElementById('chips');
function apply(){var term=q.value.trim().toLowerCase(),any=false;
document.querySelectorAll('.sec').forEach(function(s){var okG=g==='all'||s.dataset.group===g,n=0;
s.querySelectorAll('.card').forEach(function(c){var ok=okG&&(!term||c.dataset.name.indexOf(term)>-1);c.hidden=!ok;if(ok)n++});
s.hidden=n===0;if(n)any=true});
document.getElementById('none').hidden=any;chips.classList.toggle('show',g==='best'&&!term)}
document.querySelectorAll('.tabs button').forEach(function(b){b.addEventListener('click',function(){g=b.dataset.g;
document.querySelectorAll('.tabs button').forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});apply();window.scrollTo({top:0})})});
q.addEventListener('input',apply);
document.addEventListener('click',function(e){var b=e.target.closest('button[data-link]');if(!b)return;
var t=b.textContent;function done(m){b.textContent=m;setTimeout(function(){b.textContent=t},1500)}
var txt='이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\\n\\n'+b.dataset.name+'\\n'+b.dataset.link;
navigator.clipboard.writeText(txt).then(function(){done('복사됨')},function(){prompt('아래 내용을 복사하세요',txt)})});
})();
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
            items = p.best(cid)
            if items:   # 걸러 내고 남은 게 없으면 분야째 뺀다
                data["best"][name] = items
        except Exception as e:
            errors.append(f"베스트 '{name}': {e}")

    keywords = [k.strip() for k in os.environ.get("SEARCH_KEYWORDS", "").split(",") if k.strip()] or WEIRD_KEYWORDS
    start = (p.now_kst().hour * MAX_KEYWORDS) % len(keywords)   # 시간마다 다른 키워드 3개
    for kw in (keywords * 2)[start:start + min(MAX_KEYWORDS, len(keywords))]:
        try:
            data["keywords"][kw] = p.search(kw)
        except Exception as e:
            errors.append(f"검색 '{kw}': {e}")

    try:
        sports_posts = naver_posts(SPORTS_BLOG_ID)
    except Exception as ex:
        sports_posts = []
        errors.append(f"스포츠 블로그: {ex}")
    sports = (f'<section class="sec" data-group="sports" id="sports"><h2>⚽ 스포츠 뉴스</h2>'
              f'<ul class="grid">{"".join(post_card(x) for x in sports_posts)}</ul></section>') if sports_posts else ""

    try:
        car_posts = naver_posts(CAR_BLOG_ID)
    except Exception as ex:
        car_posts = []
        errors.append(f"자동차 블로그: {ex}")
    # 자동차 뉴스는 쿠팡 전체 검색창 바로 아래(맨 위)
    sections = (f'<section class="sec" data-group="car" id="car"><h2>🚗 자동차 뉴스</h2>'
                f'<ul class="grid">{"".join(post_card(x) for x in car_posts)}</ul></section>') if car_posts else ""
    for kw, items in data["keywords"].items():
        if "캠핑" in kw and items:   # 캠핑 신기템이 있으면 바로 위에
            sections += sports
            sports = ""
        sections += section(f"🔥 ‘{kw}’ 신기템", items, "weird", f"kw-{len(sections)}")
    sections += sports   # 캠핑이 없는 시간엔 신기템 묶음 바로 아래
    sections += section("⏰ 오늘의 골드박스", data["goldbox"], "goldbox", "goldbox")
    try:
        posts = naver_posts()
    except Exception as ex:
        posts = []
        errors.append(f"네이버 블로그: {ex}")
    news = (f'<section class="sec" data-group="blog" id="blog"><h2>📰 연예계 뉴스</h2>'
            f'<ul class="grid">{"".join(post_card(x) for x in posts)}</ul></section>') if posts else ""
    chips = ""
    half = len(data["best"]) // 2      # 연예계 뉴스는 페이지 중간쯤(베스트 절반 뒤)에 넣는다
    for n, (name, items) in enumerate(data["best"].items()):
        if n == half:
            sections += news
            news = ""
        sections += section(f"🏆 {name} 베스트", items[:10], "best", f"best-{n}", rank_tag)
        chips += f'<a href="#best-{n}">{html.escape(name)}</a>'
    sections += news   # 베스트가 없을 때
    if not sections:
        sections = '<p class="empty">상품을 준비하고 있어요. 잠시 뒤 다시 들러 주세요.</p>'

    page = PAGE.replace("CROWN", CROWN).replace("{chips}", chips)
    for g in ("car", "sports", "blog"):   # 빈 뉴스 탭 숨기기: 글을 못 가져온 칸은 탭도 뺀다
        if f'data-group="{g}"' not in sections:
            page = re.sub(rf'<button type="button" data-g="{g}"[^>]*>[^<]*</button>\n?', "", page)
    (OUT / "index.html").write_text(page.replace("{updated}", data["updated"]).replace("{sections}", sections),
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
