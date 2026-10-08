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


# 책(스레드 x 쿠팡파트너스) 5장·7장 방식:
#   본문 = 첫 줄 후킹 + 호기심(상품명은 숨김) + 👇
#   첫 댓글 = 대가성 문구 맨 위 + 링크
# 단, 자동으로 올리는 글이라 직접 써 보지 않은 "후기", 가짜 신분(현직 약사, 40대 주부 등),
# 근거 없는 긴박감(품절 임박 등)은 쓰지 않는다. 쿠팡 API 가 준 사실만 쓴다.
HOOKS = {
    "여성패션": ["이 가격에 이 핏이 나온다고?", "요즘 데일리룩 고민인 분들 이거 30초만 보세요", "다들 이거 하나씩은 있던데 나만 몰랐음?"],
    "남성패션": ["남자들 기본템 고민이면 이거 보세요", "이게 이 가격이라고?", "옷 고르기 귀찮은 남자분들 이거 하나면 끝"],
    "뷰티": ["화장대에 이거 없는 사람 있음?", "피부 관리 시작하려는 분들 이거 30초만 보세요", "요즘 이거 왜 이렇게 많이 사나 했더니"],
    "출산/유아동": ["아기 키우는 집이면 이거 보세요", "육아템 고민 중인 분들 이거 알아요?", "다들 이거 하나씩 쟁여두던데"],
    "식품": ["이번 주말 장보기 전에 이거 30초만 보세요", "요즘 다들 이거 쟁여두던데 나만 몰랐음?", "야식 고민인 사람만 들어오세요"],
    "주방용품": ["이게 된다고? 주방에 이거 하나 두면 달라짐", "요리 귀찮은 사람 이거 알아?", "주방 살림 바꾸고 싶은 분들 이거 보세요"],
    "생활용품": ["자취생 여러분 다이소 가기 전에 이거 30초만 보세요", "이거 없이 어떻게 살았지 싶은 생활템", "다들 이거 쓰던데 나만 몰랐음?"],
    "홈인테리어": ["방 분위기 바꾸고 싶은 분 이거 보세요", "이거 하나로 집이 달라 보인다고?", "집 꾸미기 시작한 분들 이거 알아요?"],
    "가전디지털": ["요즘 다들 이거 사던데 이유가 있었네", "가전 바꿀 때 된 분들 이거 30초만 보세요", "이게 이 가격이라고?"],
    "스포츠/레저": ["운동 시작하려는 분들 이거 알아요?", "캠핑·나들이 가기 전에 이거 보세요", "이거 챙기는 사람 vs 안 챙기는 사람"],
    "자동차용품": ["운전하시는 분들 차에 이거 있으세요?", "차에 이거 하나 두면 편하다고?", "차박·드라이브 자주 가면 이거 보세요"],
    "완구/취미": ["아이 선물 고민 중이면 이거 보세요", "이거 대체 누가 사나 했는데 다들 사더라", "새 취미 찾는 분들 이거 알아요?"],
    "문구/오피스": ["책상 위에 이거 하나 두면 달라짐", "공부·일 효율 올리고 싶은 분 이거 보세요", "다들 이거 쓰던데 나만 몰랐음?"],
    "헬스/건강식품": ["건강 챙기기 시작한 분들 이거 알아요?", "부모님 선물 고민이면 이거 보세요", "요즘 다들 이거 챙겨 먹던데"],
    "반려동물용품": ["반려동물 키우는 집이면 이거 보세요", "우리 집 아이한테 이거 있으세요?", "집사들 사이에서 많이 사는 거"],
}
LINK_LINES = 2   # 댓글에 같은 링크를 몇 줄 넣을지 (책은 2~3줄)
REPLY_LINES = ["구매 금액은 변동될 수 있어요 💸 구경만 해도 돼요😆", "실물은 링크에서 확인 👀", "가격은 링크에서 확인 💰",
               "필요한 분은 저장해 두세요 📌", "궁금한 사람만 눌러보기 👆"]
GENERIC_HOOKS = ["이게 된다고?", "이거 알아? 나만 몰랐음?", "세상에 신기한 물건 진짜 많네"]


def goldbox_hook(rate):
    try:
        r = int(float(rate))
    except (TypeError, ValueError):
        r = 0
    if r >= 50:
        return random.choice([f"쿠팡 미쳤나.. 오늘 골드박스 {r}% 할인으로 풀림;;", f"이거 오늘 반값 넘게 떨어짐;; 골드박스 {r}%"])
    return random.choice(["쿠팡 골드박스에 이게 떴네", "오늘 하루만 하는 골드박스 특가 하나 공유함"])


def compose(item, source):
    """(본문, 첫 댓글) 을 돌려준다."""
    name = str(item.get("productName", "")).strip()
    if len(name) > 80:
        name = name[:78] + "…"
    price = won(item.get("productPrice"))
    rate = item.get("discountRate")
    rank = item.get("rank")

    # 본문 1) 후킹 한 줄
    if source == "goldbox":
        hook = goldbox_hook(rate)
    else:
        hook = random.choice(HOOKS.get(source, GENERIC_HOOKS))

    # 본문 2) 호기심을 남기는 사실 1~2줄 (상품명은 본문에 쓰지 않는다)
    facts = []
    if source in HOOKS and rank:
        facts.append(f"지금 쿠팡 {source} 베스트 {rank}위에 올라와 있는 거")
    if rate and source != "goldbox":
        facts.append(f"게다가 지금 {rate}% 할인 중")
    if item.get("isRocket"):
        facts.append("로켓배송 상품이라 빨리 받아볼 수 있음")
    if not facts:
        facts.append("사진 보면 뭔지 궁금해질걸")

    body = [hook, "(쿠팡 파트너스 광고)", ""] + facts[:2] + ["", random.choice(["정체는 댓글에 👇", "뭔지는 댓글 확인 👇", "가격이랑 실물은 댓글에 👇"])]

    # 첫 댓글 (책 7.2·Step 3 형식): 대가성 문구 맨 위 → 링크 여러 줄 → 짧은 한마디.
    # 링크 카드(미리보기)는 클릭률이 높아 그대로 둔다. 상품명·가격은 카드에 나온다.
    url = item.get("productUrl", "")
    reply = [f'"{NOTICE}"'] + [f"👉 {url}"] * LINK_LINES + [random.choice(REPLY_LINES)]
    return "\n".join(body)[:MAX_TEXT], "\n".join(reply)[:MAX_TEXT]


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


def publish(text, image, reply_text):
    """본문(사진 포함)을 올리고, 그 글에 링크 댓글을 단다."""
    container = None
    if image:
        try:
            container = threads("/me/threads", {"media_type": "IMAGE", "image_url": image, "text": text})
        except RuntimeError as e:
            print("사진 글 실패, 글만 올립니다:", e)
    if not container:
        container = threads("/me/threads", {"media_type": "TEXT", "text": text})
    time.sleep(30)  # 메타 권장: 만든 뒤 처리될 때까지 잠시 기다린다
    post = threads("/me/threads_publish", {"creation_id": container["id"]})

    # 첫 댓글 (threads_manage_replies 권한 필요)
    reply = threads("/me/threads", {"media_type": "TEXT", "text": reply_text, "reply_to_id": post["id"]})
    time.sleep(10)
    threads("/me/threads_publish", {"creation_id": reply["id"]})
    return post


def main():
    posted = load_posted()
    item, source = pick(posted)
    if not item:
        p.summary("올릴 새 상품이 없습니다. 다음 수집 뒤에 다시 시도합니다.")
        return

    text, reply_text = compose(item, source)
    image = item.get("productImage") or ""
    result = publish(text, image, reply_text)

    posted.append({"id": str(item.get("productId")), "at": int(time.time()), "post": result.get("id")})
    POSTED.parent.mkdir(exist_ok=True)
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=1), encoding="utf-8")

    p.summary(f"## 스레드에 올림\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")


if __name__ == "__main__":
    main()