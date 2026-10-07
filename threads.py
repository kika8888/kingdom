"""2시간마다: 모아 둔 상품 중 아직 안 올린 것 하나를 골라 스레드에 올린다.

상품은 collect.py 가 매시간 만드는 docs/products.json 에서 고른다.
올린 상품은 state/posted.json 에 남겨 같은 상품을 반복하지 않는다.

필요한 Secrets
  THREADS_ACCESS_TOKEN   스레드 장기 토큰 (60일 유효, token-refresh 작업이 갱신)
  COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY  내 주문 상품 우선 게시용
"""
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta
from pathlib import Path

import partners as p

ROOT = Path(__file__).parent
PRODUCTS = ROOT / "docs" / "products.json"
POSTED = ROOT / "state" / "posted.json"
API = "https://graph.threads.net/v1.0"
NOTICE = "이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
KEEP_DAYS = 7          # 이 기간 안에 올린 상품은 다시 고르지 않는다
MAX_TEXT = 500         # 스레드 글자 수 제한


def threads(path, params):
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token:
        raise SystemExit("THREADS_ACCESS_TOKEN 이 설정되지 않았습니다. 저장소 Secrets 에 넣어 주세요.")
    params = dict(params, access_token=token)
    req = urllib.request.Request(f"{API}{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"스레드 API 오류 {e.code}: {detail}") from None


def won(v):
    try:
        return f"{int(float(v)):,}원"
    except (TypeError, ValueError):
        return ""


def compose(item, source):
    name = str(item.get("productName", "")).strip()
    if len(name) > 90:
        name = name[:88] + "…"
    price = won(item.get("productPrice"))
    rate = item.get("discountRate")
    extras = []
    if rate:
        extras.append(f"{rate}% 할인")
    if item.get("isRocket"):
        extras.append("로켓배송")
    if item.get("isFreeShipping"):
        extras.append("무료배송")
    extra = " · ".join(extras)

    rank = item.get("rank")
    if source == "goldbox":
        heads = ["오늘의 골드박스 특가", "오늘만 이 가격, 골드박스", "골드박스에 올라온 상품"]
    elif source in p.BEST_CATEGORIES.values():
        r = f" {rank}위" if rank else ""
        heads = [f"쿠팡 {source} 베스트{r}", f"{source} 분야 많이 팔리는 상품", f"지금 {source} 인기{r}"]
    else:
        heads = [f"'{source}' 찾는 분들 참고하세요", f"'{source}' 인기 상품", f"요즘 많이 보는 {source}"]

    lines = [NOTICE, "", random.choice(heads), "", name]
    lines.append(price + (f" ({extra})" if extra else ""))
    lines += ["", item.get("productUrl", "")]
    text = "\n".join(lines)
    return text[:MAX_TEXT]


def load_posted():
    try:
        data = json.loads(POSTED.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    cutoff = time.time() - KEEP_DAYS * 86400
    return [d for d in data if d.get("at", 0) > cutoff]


def my_sold_ids():
    """최근 30일 동안 내 링크로 실제 주문된 상품 ID. 실패해도 게시는 계속한다."""
    try:
        end = p.now_kst()
        rows = p.report("orders", (end - timedelta(days=30)).strftime("%Y%m%d"), end.strftime("%Y%m%d"))
        return {str(r.get("productId")) for r in rows if r.get("productId")}
    except Exception as e:
        print("주문 리포트 조회 실패(무시):", e)
        return set()


def rank_of(item):
    try:
        return int(item.get("rank") or 999)
    except (TypeError, ValueError):
        return 999


def pick(posted):
    """잘 팔리는 상품부터 고른다. 파트너스 API 에는 매출 숫자가 없어서 아래 순서로 대신한다.
       1. 내 링크로 최근 30일 안에 실제 주문된 상품
       2. 카테고리 베스트 상위 10위 (쿠팡 판매 인기 순위)
       3. 관심 키워드 검색 상위 5위
       4. 골드박스
    """
    try:
        data = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit("docs/products.json 이 없습니다. '상품 수집' 작업을 먼저 한 번 실행해 주세요.")
    seen = {str(d.get("id")) for d in posted}
    sold = my_sold_ids()

    everything = [(i, "goldbox") for i in data.get("goldbox", [])]
    for kw, items in data.get("keywords", {}).items():
        everything += [(i, kw) for i in items]
    for cat, items in data.get("best", {}).items():
        everything += [(i, cat) for i in items]
    fresh = [(i, s) for i, s in everything if str(i.get("productId")) not in seen and i.get("productUrl")]

    best_names = set(data.get("best", {}))
    kw_names = set(data.get("keywords", {}))
    tiers = [
        [x for x in fresh if str(x[0].get("productId")) in sold],
        [x for x in fresh if x[1] in best_names and rank_of(x[0]) <= 10],
        [x for x in fresh if x[1] in kw_names and rank_of(x[0]) <= 5],
        [x for x in fresh if x[1] == "goldbox"],
        fresh,
    ]
    for tier in tiers:
        if tier:
            tier.sort(key=lambda x: rank_of(x[0]))
            return random.choice(tier[:5])  # 상위 몇 개 안에서 골라 같은 분야만 반복되지 않게
    return None, None


def publish(text, image):
    """사진 글을 먼저 시도하고, 사진이 거절되면 글만 올린다."""
    container = None
    if image:
        try:
            container = threads("/me/threads", {"media_type": "IMAGE", "image_url": image, "text": text})
        except RuntimeError as e:
            print("사진 글 실패, 글만 올립니다:", e)
    if not container:
        container = threads("/me/threads", {"media_type": "TEXT", "text": text})
    time.sleep(30)  # 메타 권장: 만든 뒤 처리될 때까지 잠시 기다린다
    return threads("/me/threads_publish", {"creation_id": container["id"]})


def main():
    posted = load_posted()
    item, source = pick(posted)
    if not item:
        p.summary("올릴 새 상품이 없습니다. 다음 수집 뒤에 다시 시도합니다.")
        return

    text = compose(item, source)
    image = item.get("productImage") or ""
    result = publish(text, image)

    posted.append({"id": str(item.get("productId")), "at": int(time.time()), "post": result.get("id")})
    POSTED.parent.mkdir(exist_ok=True)
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=1), encoding="utf-8")

    p.summary(f"## 스레드에 올림\n\n```\n{text}\n```")


if __name__ == "__main__":
    main()
