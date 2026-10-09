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
PICKS = ROOT / "picks.txt"   # 직접 고른 상품 (2순위)
VIDEOS = ROOT / "videos.txt"   # 캡컷 영상 목록 (1순위). 영상 파일은 docs/videos/ 에 둔다
SITE = "https://kingdom.papalaqi.com"
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


def threads_get(path, params):
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    q = urllib.parse.urlencode(dict(params, access_token=token))
    try:
        with urllib.request.urlopen(f"{API}{path}?{q}", timeout=30) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"스레드 API 오류 {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None


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
# 댓글 링크 카드 모양: "coupang" = 쿠팡 로고가 크게 나오는 카드 (책 예시), "product" = 상품 사진 카드
CARD_STYLE = "coupang"
LINK_LINES = 2   # 댓글에 같은 링크를 몇 줄 넣을지 (책은 2~3줄)
REPLY_LINES = ["구매 금액은 변동될 수 있어요 💸 구경만 해도 돼요😆", "실물은 링크에서 확인 👀", "가격은 링크에서 확인 💰",
               "필요한 분은 저장해 두세요 📌", "궁금한 사람만 눌러보기 👆"]
GENERIC_HOOKS = ["이게 된다고?", "이거 알아? 나만 몰랐음?", "세상에 신기한 물건 진짜 많네"]
# 해시태그: 분야/키워드 1개 + 상품명 단어 2개 + 아래에서 채워 5개.
# 스레드는 첫 번째 해시태그만 주제 태그로 잡으니 분야 태그를 맨 앞에 둔다.
TAG_COUNT = 5
TAG_POOL = ["쿠팡추천", "꿀템", "살림템", "신기템", "쿠팡템", "생활꿀팁", "아이디어상품"]
TAG_SKIP = {"1개", "2개", "3개", "세트", "증정", "랜덤", "무료배송", "로켓배송"}


def tag_word(s):
    return "".join(ch for ch in str(s) if ch.isalnum())


def hashtags(item, source):
    first = {"goldbox": "골드박스", "manual": "신기템", "video": "신기템영상"}.get(source, source)
    words = [tag_word(w) for w in str(item.get("productName", "")).split(",")[0].split()]
    if len(words) >= 3:
        words = words[1:]   # 첫 단어는 대개 브랜드
    words = [w for w in words if len(w) >= 3 and not any(c.isdigit() for c in w) and w not in TAG_SKIP]
    words.sort(key=len, reverse=True)   # 긴 단어일수록 품목 이름(위생장갑, 유아물티슈)
    tags = []
    for t in [tag_word(first)] + words[:2] + random.sample(TAG_POOL, len(TAG_POOL)):
        if t and t not in tags:
            tags.append(t)
    return " ".join("#" + t for t in tags[:TAG_COUNT])


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
    if source in ("manual", "video"):
        hook = item.get("memo") or random.choice(GENERIC_HOOKS)
    elif source == "goldbox":
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
    if source == "manual":
        facts.append("직접 찾은 신기템 공유함")
    if source == "video":
        facts.append("영상으로 직접 보여 드려요")
    if not facts:
        facts.append("사진 보면 뭔지 궁금해질걸")

    # 광고 표시는 지우지 않는다 (공정위 지침·파트너스 약관). 해시태그 사이에 섞으면 인정되지 않아 따로 한 줄.
    if source == "video" and not item.get("productUrl"):   # 링크 없는 영상: 댓글 안내·광고 표시 없이
        body = [hook, ""] + facts[:2] + ["", hashtags(item, source)]
        return "\n".join(body)[:MAX_TEXT], ""
    body = [hook, ""] + facts[:2] + ["", random.choice(["정체는 댓글에 👇", "뭔지는 댓글 확인 👇", "가격이랑 실물은 댓글에 👇"]),
                                     "", hashtags(item, source), "#광고"]

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
    # 영상은 한 번만 올린다 (7일이 지나도 기록을 지우지 않음)
    return [d for d in data if d.get("at", 0) > cutoff or str(d.get("id", "")).startswith("video:")]


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
       2. 희귀템·관심 키워드 검색 상위 5위
       3. 카테고리 베스트 상위 10위 (쿠팡 판매 인기 순위)
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
        [x for x in fresh if x[1] in kw_names and rank_of(x[0]) <= 5],
        [x for x in fresh if x[1] in best_names and rank_of(x[0]) <= 10],
        [x for x in fresh if x[1] == "goldbox"],
        fresh,
    ]
    for tier in tiers:
        if tier:
            tier.sort(key=lambda x: rank_of(x[0]))
            return random.choice(tier[:5])  # 상위 몇 개 안에서 골라 같은 분야만 반복되지 않게
    return None, None


def pick_manual(posted):
    """picks.txt 에 직접 넣은 쿠팡 주소 중 아직 안 올린 첫 번째. (주소 | 첫 줄 문구)"""
    try:
        lines = PICKS.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None, None
    seen = {str(d.get("id")) for d in posted}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        url, _, memo = (s.strip() for s in line.partition("|"))
        if url.startswith("http") and url not in seen:
            links = p.deeplink([url])
            short = links[0].get("shortenUrl") if links else ""
            if not short:
                print("파트너스 링크를 만들지 못한 주소(건너뜀):", url)
                continue
            return {"productId": url, "productUrl": short, "productName": "", "productImage": "", "memo": memo}, "manual"
    return None, None


def pick_video(posted):
    """videos.txt 에 적은 영상 중 아직 안 올린 첫 번째. (파일이름 | 쿠팡 주소 | 첫 줄 문구)"""
    try:
        lines = VIDEOS.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None, None
    seen = {str(d.get("id")) for d in posted}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [s.strip() for s in line.split("|")] + ["", ""]
        name, url, memo = parts[0], parts[1], parts[2]
        if f"video:{name}" in seen:
            continue
        if not (ROOT / "docs" / "videos" / name).exists():
            print("영상 파일이 docs/videos 에 없습니다(건너뜀):", name)
            continue
        video = f"{SITE}/videos/{urllib.parse.quote(name)}"
        if not online(video):   # 방금 올린 영상은 사이트 반영(1~2분) 전이라 메타가 못 가져간다. 다음 차례에 올린다
            print("영상이 아직 사이트에 반영되지 않았습니다(다음에 올림):", video)
            continue
        short = ""
        if url.startswith("http"):
            links = p.deeplink([url])
            short = links[0].get("shortenUrl") if links else ""
        return {"productId": f"video:{name}", "productUrl": short, "productName": "", "productImage": "",
                "video": video, "memo": memo}, "video"
    return None, None


def online(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status == 200
    except Exception:
        return False


def short_link(item):
    """API 가 주는 긴 추적 링크 대신 책처럼 link.coupang.com/a/xxxx 짧은 링크를 만든다."""
    pid = item.get("productId")
    if not pid or str(pid).startswith("http"):
        return item.get("productUrl", "")
    page = f"https://www.coupang.com/vp/products/{pid}"
    try:
        links = p.deeplink([page])
        short = links[0].get("shortenUrl") if links else ""
        return short or item.get("productUrl", "")
    except Exception as e:
        print("짧은 링크 실패, 원래 링크 사용:", e)
        return item.get("productUrl", "")


def coupang_card_link(item):
    """쿠팡 검색 페이지를 파트너스 링크로 만든다. 이 링크로 카드를 띄우면 쿠팡 로고가 크게 나온다."""
    words = str(item.get("productName", "")).split(",")[0].split()[:4]
    if not words:
        return ""
    page = "https://www.coupang.com/np/search?q=" + urllib.parse.quote(" ".join(words))
    try:
        links = p.deeplink([page])
        return (links[0].get("shortenUrl") if links else "") or ""
    except Exception as e:
        print("로고 카드 링크 실패, 상품 카드로 올립니다:", e)
        return ""


def publish(text, image, reply_text, card_url="", video=""):
    """본문(영상 또는 사진 포함)을 올리고, 그 글에 링크 댓글을 단다."""
    container = None
    if video:
        container = threads("/me/threads", {"media_type": "VIDEO", "video_url": video, "text": text})
        for _ in range(30):   # 영상은 메타가 처리할 때까지 최대 5분 기다린다
            time.sleep(10)
            st = threads_get(f"/{container['id']}", {"fields": "status,error_message"})
            if st.get("status") == "FINISHED":
                break
            if st.get("status") == "ERROR":
                raise RuntimeError(f"영상 처리 실패: {st.get('error_message')}")
        else:
            raise RuntimeError("영상 처리가 5분 안에 끝나지 않았습니다")
    elif image:
        try:
            container = threads("/me/threads", {"media_type": "IMAGE", "image_url": image, "text": text})
        except RuntimeError as e:
            print("사진 글 실패, 글만 올립니다:", e)
    if not container:
        container = threads("/me/threads", {"media_type": "TEXT", "text": text})
    if not video:
        time.sleep(30)  # 메타 권장: 만든 뒤 처리될 때까지 잠시 기다린다
    post = threads("/me/threads_publish", {"creation_id": container["id"]})
    if not reply_text:
        return post

    # 첫 댓글 (threads_manage_replies 권한 필요)
    params = {"media_type": "TEXT", "text": reply_text, "reply_to_id": post["id"]}
    if card_url:
        params["link_attachment"] = card_url   # 카드만 이 링크로 (본문 링크는 그대로)
    reply = threads("/me/threads", params)
    time.sleep(10)
    threads("/me/threads_publish", {"creation_id": reply["id"]})
    return post


def post_video(posted):
    """영상 1순위. 올렸으면 True. 실패한 영상은 기록해 두고 다시 고르지 않는다(막히지 않게)."""
    item, source = pick_video(posted)
    if not item:
        return False
    text, reply_text = compose(item, source)
    try:
        result = publish(text, "", reply_text, "", item["video"])
    except RuntimeError as e:
        posted.append({"id": item["productId"], "at": int(time.time()), "failed": str(e)[:200]})
        save_posted(posted)
        p.summary(f"## 영상 게시 실패 (상품 글로 대신 올림)\n\n- {item['productId'][6:]}: {e}\n"
                  "- 영상을 고쳐 **새 파일 이름**으로 올리고 videos.txt 에 새 줄로 적어 주세요.")
        return False
    posted.append({"id": item["productId"], "at": int(time.time()), "post": result.get("id")})
    save_posted(posted)
    p.summary(f"## 스레드에 영상 올림\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")
    return True


def save_posted(posted):
    POSTED.parent.mkdir(exist_ok=True)
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    posted = load_posted()
    if post_video(posted):
        return
    item, source = pick_manual(posted)
    if not item:
        item, source = pick(posted)
        if item:
            item = dict(item, productUrl=short_link(item))
    if not item:
        p.summary("올릴 새 상품이 없습니다. 다음 수집 뒤에 다시 시도합니다.")
        return

    text, reply_text = compose(item, source)
    image = item.get("productImage") or ""
    card_url = coupang_card_link(item) if CARD_STYLE == "coupang" else ""
    result = publish(text, image, reply_text, card_url)

    posted.append({"id": str(item.get("productId")), "at": int(time.time()), "post": result.get("id")})
    save_posted(posted)

    p.summary(f"## 스레드에 올림\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")


if __name__ == "__main__":
    main()