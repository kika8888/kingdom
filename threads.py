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
# 해시태그: 분야/키워드 1개만. 스레드는 첫 번째 해시태그만 주제 태그로 잡고,
# 나머지(#만들어주는 #수선패드 …)는 글자로 남아 광고 계정처럼 보여서 퍼지지 않는다 (2026-10-13).
TAG_COUNT = 1
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


# 말투: 올릴 때마다 바로 전과 다른 말투를 고른다 (posted.json 에 tone 기록).
# {t} = 분야·키워드 이름, {r} = 순위, {p} = 할인율, {n} = 상품 개수, {title} = 영상 제목
# 자동 글이라 직접 써 본 척하는 후기·가짜 신분·근거 없는 품절 임박 같은 말은 넣지 않는다.
TONES = {
    "친구": {
        "yt": ["영상으로 비교해봤어", "이거 영상 보면 바로 이해됨", "직접 정리한 영상 올려봄", "고민되면 이 영상 하나면 끝"],
        "yt_cta": "영상 속 상품 링크는 댓글에 👇",
        "hook": ["야 이거 봤어?", "{t} 찾는 사람 이거 봐봐", "이거 나만 몰랐냐", "요즘 {t} 이거 많이 사더라",
                 "이거 왜 이제 알았지", "너 이거 알고 있었어?", "이런 게 있는 줄 몰랐네", "이거 하나 있으면 편하겠다",
                 "{t} 이거 어때?", "오 이거 괜찮은데?", "이거 은근 많이 쓰더라", "이거 보자마자 생각났어"],
        "gold": ["오늘 골드박스에 이거 떴어", "골드박스 {p}% 떴다 이거"],
        "rank": "지금 쿠팡 {t} 베스트 {r}위래", "sale": "지금 {p}% 할인 중이래", "rocket": "로켓배송이라 금방 와",
        "manual": "내가 찾은 신기템 공유함", "video": "영상으로 보여줄게", "none": "사진 보면 뭔지 궁금할걸",
        "cta": ["뭔지는 댓글에 👇", "궁금하면 댓글 봐 👇"],
        "reply": ["필요하면 저장해둬 📌", "구경만 해도 됨 😆", "가격은 링크에서 봐 💰"],
        "top": ["요즘 {t} 제일 잘 나가는 거 {n}개", "{t} 인기템 {n}개 모아봤어"], "top_sub": "순위대로 영상으로 정리함",
        "intro": "{title}. 인기 상품 {n}개 바로 알려줄게", "outro": "맘에 드는 거 있으면 댓글 링크 봐봐",
        "outro_title": "맘에 드는 거 있었어?", "end": "자세한 건 댓글 링크 봐봐",
    },
    "존댓말": {
        "yt": ["영상으로 비교해 정리했어요", "고민되시면 이 영상 한번 보세요", "영상으로 차이를 보여 드릴게요", "한눈에 비교할 수 있게 영상으로 담았어요"],
        "yt_cta": "영상 속 상품 링크는 댓글에 있어요 👇",
        "hook": ["{t} 고민 중이시면 이거 한번 보세요", "요즘 {t} 이 상품 많이 찾으시더라고요", "혹시 이거 알고 계셨어요?",
                 "이런 상품도 있더라고요", "오늘은 이 상품 소개해 드릴게요", "{t} 찾으시는 분들께 추천드려요",
                 "생각보다 유용한 상품이에요", "알아두면 좋은 상품 하나 공유드려요", "요즘 많이들 쓰시는 거예요",
                 "{t} 쪽에서 눈에 띈 상품이에요", "한번쯤 보셔도 좋을 상품이에요"],
        "gold": ["오늘 쿠팡 골드박스에 올라온 상품이에요", "오늘 골드박스 {p}% 특가 상품 공유드려요"],
        "rank": "지금 쿠팡 {t} 베스트 {r}위에 올라와 있어요", "sale": "지금 {p}% 할인 중이에요",
        "rocket": "로켓배송이라 빨리 받아보실 수 있어요", "manual": "직접 찾은 신기템 공유드려요",
        "video": "영상으로 보여 드릴게요", "none": "사진 보시면 뭔지 궁금해지실 거예요",
        "cta": ["자세한 건 댓글에 있어요 👇", "가격이랑 실물은 댓글에서 확인하세요 👇"],
        "reply": ["필요하신 분은 저장해 두세요 📌", "구매 금액은 변동될 수 있어요 💸", "실물은 링크에서 확인하세요 👀"],
        "top": ["쿠팡 {t} 인기 상품 {n}개 정리했어요", "{t} 고민이시면 이 {n}개만 보세요"], "top_sub": "순위대로 영상으로 정리했어요",
        "intro": "{title}. 인기 상품 {n}개 바로 알려드릴게요", "outro": "마음에 드는 거 있으면 댓글 링크에서 확인해 보세요",
        "outro_title": "마음에 드는 거 있었나요?", "end": "자세한 정보는 댓글 링크에서 확인해 보세요",
    },
    "감탄": {
        "yt": ["와 이렇게 비교하니까 확 보이네", "영상으로 보니까 차이가 엄청남", "이거 영상으로 봐야 함", "비교해보고 깜짝 놀람"],
        "yt_cta": "영상 속 상품은 댓글에 👇",
        "hook": ["와 이게 된다고?", "세상에 이런 게 있었네", "이거 진짜 신기하다;;", "와 {t} 이런 것도 있구나",
                 "이걸 이렇게 만든다고?", "아이디어 미쳤다", "이거 처음 보고 놀람", "와 이건 좀 신박한데?",
                 "누가 이런 생각을 했지", "이게 진짜 있네;;", "와 세상 좋아졌다", "이거 보고 감탄함"],
        "gold": ["와 골드박스 {p}%라고?", "오늘 골드박스 이거 실화임?"],
        "rank": "무려 쿠팡 {t} 베스트 {r}위", "sale": "심지어 {p}% 할인 중", "rocket": "로켓배송까지 됨",
        "manual": "찾다가 신기해서 가져옴", "video": "영상으로 봐야 더 신기함", "none": "사진만 봐도 신기함",
        "cta": ["정체는 댓글에 👇", "뭔지 궁금하면 댓글 👇"],
        "reply": ["신기하면 저장 📌", "구경만 해도 재밌음 😆", "실물 궁금하면 눌러봐 👀"],
        "top": ["와 요즘 {t} 이게 제일 잘 나간대", "{t} 인기템 {n}개 보고 놀람"], "top_sub": "순위별로 영상에 담았음",
        "intro": "{title}. 와 이거 보세요, {n}개 바로 갑니다", "outro": "신기한 거 있었으면 댓글 링크 확인해 보세요",
        "outro_title": "신기한 거 있었어?", "end": "궁금하면 댓글 링크 확인해 보세요",
    },
    "질문": {
        "yt": ["뭐가 제일 나은지 영상으로 볼래요?", "이 중에 뭐 고르실 거예요?", "비교 영상 보셨어요?", "어떤 게 제일 마음에 드세요?"],
        "yt_cta": "상품 링크는 댓글에서 확인하세요 👇",
        "hook": ["{t} 아직도 고민 중이세요?", "이거 있는 집 손?", "이거 뭔지 아는 사람?", "다들 {t} 뭐 쓰세요?",
                 "이거 어디에 쓰는 건지 맞혀 보실래요?", "이런 거 필요했던 적 있으세요?", "혹시 이거 써 본 사람?",
                 "이거 본 적 있어요?", "{t} 뭐 살지 모르겠을 때 어떡해요?", "이거 집에 하나쯤 있어야 하지 않나요?",
                 "이거 왜 인기 있는지 아세요?"],
        "gold": ["오늘 골드박스 보셨어요?", "골드박스 {p}% 이거 아셨어요?"],
        "rank": "쿠팡 {t} 베스트 {r}위인 거 아셨어요?", "sale": "지금 {p}% 할인 중인 건요?",
        "rocket": "로켓배송이라 빨리 오는 것도요", "manual": "이런 신기템 보셨어요?", "video": "영상으로 보실래요?",
        "none": "사진 보면 뭔지 아시겠어요?",
        "cta": ["정답은 댓글에 👇", "궁금하면 댓글 확인 👇"],
        "reply": ["필요하면 저장해 두실래요? 📌", "구경만 해도 괜찮아요 😆", "가격 궁금하면 눌러보세요 💰"],
        "top": ["요즘 {t} 뭐가 제일 잘 나가는지 아세요?", "{t} 인기템 {n}개 아세요?"], "top_sub": "순위대로 영상에서 확인해 보세요",
        "intro": "{title}. 뭐가 제일 잘 나가는지 아세요? {n}개 알려드릴게요", "outro": "마음에 드는 거 있으셨어요? 댓글 링크 확인해 보세요",
        "outro_title": "마음에 드는 거 있으셨어요?", "end": "궁금하면 댓글 링크 확인해 보세요",
    },
    "짧게": {
        "yt": ["비교 영상", "영상으로 정리", "한눈에 비교", "영상 하나로 끝"],
        "yt_cta": "링크는 댓글 👇",
        "hook": ["이거.", "{t} 이거 하나면 됨", "요즘 이거", "그냥 이거 보세요", "이거 괜찮음", "{t} 추천",
                 "오늘의 발견", "이거 알아두기", "저장각", "요즘 인기템", "한 줄 요약: 편함"],
        "gold": ["골드박스 {p}%", "오늘 골드박스"],
        "rank": "쿠팡 {t} 베스트 {r}위", "sale": "{p}% 할인 중", "rocket": "로켓배송", "manual": "신기템 발견",
        "video": "영상으로", "none": "궁금하면",
        "cta": ["댓글 👇", "링크는 댓글 👇"],
        "reply": ["저장 📌", "구경만 😆", "가격은 링크 💰"],
        "top": ["{t} TOP {n}", "{t} 인기템 {n}개"], "top_sub": "순위대로 정리",
        "intro": "{title}. {n}개 갑니다", "outro": "링크는 댓글에",
        "outro_title": "어떤 게 좋아요?", "end": "링크는 댓글에",
    },
}


def first_line(text):
    return text.splitlines()[0] if text else ""


def pick_tone(posted):
    last = next((d.get("tone") for d in reversed(posted) if d.get("tone")), None)
    return random.choice([t for t in TONES if t != last])


USED = set()   # 최근 7일 동안 쓴 첫 줄. main() 이 채운다. 같은 첫 줄을 다시 쓰지 않게


def say(tone, key, **kw):
    v = TONES[tone][key]
    if not isinstance(v, list):
        return v.format(**kw)
    options = [o.format(**kw) for o in v]
    fresh = [o for o in options if o not in USED]
    return random.choice(fresh or options)


def goldbox_hook(rate, tone):
    try:
        r = int(float(rate))
    except (TypeError, ValueError):
        r = 0
    if r:
        return say(tone, "gold", p=r)
    return [g for g in TONES[tone]["gold"] if "{p}" not in g][0]


TONE = "존댓말"   # main() 이 이번 글의 말투로 바꾼다


def compose(item, source):
    """(본문, 첫 댓글) 을 돌려준다."""
    name = str(item.get("productName", "")).strip()
    if len(name) > 80:
        name = name[:78] + "…"
    price = won(item.get("productPrice"))
    rate = item.get("discountRate")
    rank = item.get("rank")

    tone = TONE
    topic = "신기템" if source in ("manual", "video") else source

    # 본문 1) 후킹 한 줄 (말투마다 다르게. 존댓말일 땐 분야 전용 문구도 섞는다)
    if source in ("manual", "video") and item.get("memo"):
        hook = item["memo"]
    elif source == "goldbox":
        hook = goldbox_hook(rate, tone)
    elif tone == "존댓말" and source in HOOKS and random.random() < 0.5:
        hook = random.choice(HOOKS[source])
    else:
        hook = say(tone, "hook", t=topic)

    # 본문 2) 호기심을 남기는 사실 1~2줄 (상품명은 본문에 쓰지 않는다)
    facts = []
    if source in HOOKS and rank:
        facts.append(say(tone, "rank", t=source, r=rank))
    if rate and source != "goldbox":
        facts.append(say(tone, "sale", p=rate))
    if item.get("isRocket"):
        facts.append(say(tone, "rocket"))
    if source in ("manual", "video"):
        facts.append(say(tone, source))
    if not facts:
        facts.append(say(tone, "none"))

    # 광고 표시는 지우지 않는다 (공정위 지침·파트너스 약관). 해시태그 사이에 섞으면 인정되지 않아 따로 한 줄.
    if source == "video" and not item.get("productUrl"):   # 링크 없는 영상: 댓글 안내·광고 표시 없이
        body = [hook, ""] + facts[:2] + ["", hashtags(item, source)]
        return "\n".join(body)[:MAX_TEXT], ""
    body = [hook, ""] + facts[:2] + ["", say(tone, "cta"), "", hashtags(item, source), "#광고"]

    # 첫 댓글 (책 7.2·Step 3 형식): 대가성 문구 맨 위 → 링크 여러 줄 → 짧은 한마디.
    # 링크 카드(미리보기)는 클릭률이 높아 그대로 둔다. 상품명·가격은 카드에 나온다.
    url = item.get("productUrl", "")
    reply = [f'"{NOTICE}"'] + [f"👉 {url}"] * LINK_LINES + [say(tone, "reply")]
    return "\n".join(body)[:MAX_TEXT], "\n".join(reply)[:MAX_TEXT]


def load_posted():
    try:
        data = json.loads(POSTED.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    cutoff = time.time() - KEEP_DAYS * 86400
    # 영상은 한 번만 올린다 (7일이 지나도 기록을 지우지 않음)
    return [d for d in data if d.get("at", 0) > cutoff or str(d.get("id", "")).startswith(("video:", "yt:"))]


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
    """picks.txt 에 직접 넣은 쿠팡 주소 중 아직 안 올린 첫 번째. (주소 | 첫 줄 문구 | 영상)
    셋째 칸에 '영상' 이라고 적으면 사진 글 대신 자동 쇼츠 영상으로 올린다."""
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
        memo, _, flag = (s.strip() for s in memo.partition("|"))
        flag, _, hint = (s.strip() for s in flag.partition("|"))   # 넷째 칸: 상품 링크일 때 사진 찾을 검색어
        name = hint if url.startswith("http") else url
        if url and not url.startswith("http"):   # 휴대폰에서 상품 이름만 적어도 쿠팡 검색 링크로 바꾼다
            url = "https://www.coupang.com/np/search?q=" + urllib.parse.quote(url)
        if url.startswith("http") and url not in seen:
            short = partner_link(url)
            if not short:
                print("파트너스 링크를 만들지 못한 주소(건너뜀):", url)
                continue
            return {"productId": url, "productUrl": short, "productName": name, "productImage": manual_image(url, hint),
                    "memo": memo, "video": flag == "영상"}, "manual"
    return None, None


def partner_link(url):
    """직접 넣은 쿠팡 주소를 파트너스 짧은 링크로. 쿠팡이 거절하면(url convert failed 등)
    주소 뒤 ?itemId=... 를 떼고 한 번 더 해 보고, 그래도 안 되면 "" (게시 전체가 멈추지 않게)."""
    tries = [url]
    if "/vp/products/" in url and "?" in url:
        tries.append(url.split("?")[0])
    for u in tries:
        try:
            links = p.deeplink([u])
        except Exception as e:
            print("파트너스 링크 실패:", u, e)
            continue
        short = links[0].get("shortenUrl") if links else ""
        if short:
            return short
    return ""


def manual_image(url, hint=""):
    """picks 상품 사진: 검색 링크면 그 검색어로, 상품 링크면 넷째 칸 검색어(hint)로 검색해서
    같은 상품 번호 → 이름에 검색어가 든 상품 순으로 찾는다."""
    q = urllib.parse.urlparse(url)
    word = urllib.parse.parse_qs(q.query).get("q", [""])[0]
    pid = q.path.split("/vp/products/")[1].split("/")[0] if "/vp/products/" in q.path else ""
    word = hint or word or pid
    if not word:
        return ""
    try:
        items = p.search(word, limit=10)
    except Exception as e:
        print("picks 사진 찾기 실패(글만 올림):", e)
        return ""
    for it in items or []:
        if pid and str(it.get("productId")) == pid and it.get("productImage"):
            return it["productImage"]
    # 검색 1위가 다른 상품일 수 있다 (몽쉘을 찾았는데 초코파이가 1위). 이름에 검색어 첫 단어가 들어간 상품만 쓴다.
    # 맞는 사진이 없으면 사진 없이 글만 올린다 (엉뚱한 사진보다 낫다).
    key = "" if word.isdigit() else word.split()[0].lower()   # 상품 번호로만 찾았으면 번호가 같은 것만 인정
    for it in items or []:
        if key and it.get("productImage") and key in str(it.get("productName", "")).lower().replace(" ", ""):
            return it["productImage"]
    print("picks 사진: 검색어와 이름이 맞는 상품이 없어 사진 없이 올립니다:", word)
    return ""


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
            short = partner_link(url)
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
    try:   # 본문은 이미 올라갔으니 댓글이 실패해도 같은 글을 다시 올리지 않는다
        reply = threads("/me/threads", params)
        time.sleep(10)
        threads("/me/threads_publish", {"creation_id": reply["id"]})
    except RuntimeError as e:
        p.summary(f"### 링크 댓글 실패 (본문은 올라감)\n- {e}")
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
    posted.append({"id": item["productId"], "at": int(time.time()), "tone": TONE, "hook": first_line(text),
                   "post": result.get("id")})
    save_posted(posted)
    p.summary(f"## 스레드에 영상 올림\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")
    return True


AUTO_EVERY = 2   # 글 2개 중 1개는 자동 영상(사진 + 한국어 여성 목소리 + 배경음)으로


def auto_turn(posted):
    """마지막 자동 영상 뒤로 글이 AUTO_EVERY-1 개 이상 올라갔으면 이번이 영상 차례."""
    done = [d for d in posted if "failed" not in d]
    since = 0
    for d in reversed(done):
        if d.get("auto"):
            break
        since += 1
    return since >= AUTO_EVERY - 1


TOP_N = 3


def pick_top(posted):
    """같은 분야(베스트) 또는 같은 키워드에서 아직 안 올린 사진 있는 상품 3개. 인기순."""
    try:
        data = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    seen = {str(d.get("id")) for d in posted}
    groups = [(cat, items, "best") for cat, items in data.get("best", {}).items()]
    groups += [(kw, items, "keyword") for kw, items in data.get("keywords", {}).items()]
    random.shuffle(groups)
    for name, items, kind in groups:
        fresh = [i for i in items if str(i.get("productId")) not in seen and i.get("productUrl") and i.get("productImage")]
        fresh.sort(key=rank_of)
        if len(fresh) >= TOP_N and all(rank_of(i) < 999 for i in fresh[:TOP_N]):
            return name, kind, fresh[:TOP_N]
    return None


def compose_top(name, kind, items, urls):
    tone = TONE
    hook = say(tone, "top", t=name if kind == "best" else f"'{name}'", n=len(items))
    labels = [f"{'베스트' if kind == 'best' else '검색'} {rank_of(i)}위" for i in items]
    body = [hook, "", say(tone, "top_sub"), "", say(tone, "cta"), "", hashtags(items[0], name), "#광고"]
    reply = [f'"{NOTICE}"', ""] + [f"{lab} 👉 {u}" for lab, u in zip(labels, urls)] + ["", say(tone, "reply")]
    return hook, labels, "\n".join(body)[:MAX_TEXT], "\n".join(reply)[:MAX_TEXT]


def post_top(posted):
    """TOP 3 영상 글. 올렸으면 True, 못 만들면 False (그 차례는 다른 글로)."""
    import make_video
    top = pick_top(posted)
    if not top:
        return False
    name, kind, items = top
    urls = [short_link(i) for i in items]
    hook, labels, text, reply_text = compose_top(name, kind, items, urls)
    title = f"쿠팡 {name} 베스트" if kind == "best" else f"'{name}' 인기템"
    words = {k: say(TONE, k, title=title, n=len(items)) for k in ("intro", "outro", "outro_title")}
    try:
        video = push_video(f"auto-top-{items[0].get('productId')}.mp4",
                           lambda out: make_video.make_top(title, items, labels, out, words))
        result = publish(text, "", reply_text, coupang_card_link(items[0]), video)
    except Exception as e:
        print("TOP 영상 실패, 다른 글로 올립니다:", e)
        p.summary(f"### TOP 영상 실패 (다른 글로 대신 올림)\n- {e}")
        return False
    now = int(time.time())
    posted += [{"id": str(i.get("productId")), "at": now, "auto": True, "tone": TONE, "hook": first_line(text),
                "post": result.get("id")}
               for i in items]
    save_posted(posted)
    p.summary(f"## 스레드에 TOP 영상 올림\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")
    return True


def auto_video(item, text):
    """상품 1개 영상 (TOP 3 를 못 모을 때)."""
    import make_video
    lines = text.split("\n")
    hook = lines[0]
    facts = lines[2:lines.index("", 2)] if "" in lines[2:] else lines[2:3]
    end = say(TONE, "end")
    pid = str(item.get("productId"))
    if not pid.isdigit():   # picks 는 productId 가 쿠팡 주소라 파일 이름으로 못 쓴다
        import hashlib
        pid = "pick-" + hashlib.md5(pid.encode()).hexdigest()[:10]
    return push_video(f"auto-{pid}.mp4", lambda out: make_video.make(item, hook, facts, out, end))


def push_video(name, build):
    """영상을 만들어 docs/videos 에 올리고(push), 사이트에 반영되면 주소를 돌려준다."""
    import subprocess
    folder = ROOT / "docs" / "videos"
    folder.mkdir(parents=True, exist_ok=True)
    git = ["git", "-c", "user.name=kingdom-bot", "-c", "user.email=kingdom-bot@users.noreply.github.com"]
    for old in folder.glob("auto-*.mp4"):   # 지난 자동 영상은 스레드가 이미 가져갔으니 지워서 저장소를 가볍게
        old.unlink()
    try:
        build(folder / name)
    except Exception:
        # 실패하면 지운 파일을 되돌린다. 안 그러면 뒤의 기록 저장(git pull --rebase)이 '변경 사항 있음'으로 실패한다
        subprocess.run(git + ["checkout", "--", "docs/videos"], cwd=ROOT, capture_output=True)
        for f in folder.glob("auto-*"):
            if subprocess.run(git + ["ls-files", "--error-unmatch", str(f)], cwd=ROOT, capture_output=True).returncode:
                f.unlink()
        raise

    for cmd in (["add", "-A", "docs/videos"], ["commit", "-m", "auto video"], ["pull", "--rebase"], ["push"]):
        r = subprocess.run(git + cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {cmd[0]} 실패: {(r.stderr or r.stdout).strip()[:200]}")
    url = f"{SITE}/videos/{name}"
    for _ in range(24):   # 사이트 반영 최대 6분 기다림
        time.sleep(15)
        if online(url):
            return url
    raise RuntimeError("영상이 사이트에 반영되지 않았습니다")


def save_posted(posted):
    POSTED.parent.mkdir(exist_ok=True)
    POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=1), encoding="utf-8")


YT_LIST = ROOT / "youtube_videos.json"   # 내 채널 공개 영상 (제목·요약·영상 속 상품 링크)
YT_EVERY = 6   # 글 6개 중 1개는 내 영상 링크 글
YT_REUSE_DAYS = 60   # 영상을 다 올린 뒤 다시 쓸 때, 이 기간 안에 올린 영상은 건너뛴다


def yt_turn(posted):
    """마지막 영상 링크 글 뒤로 글이 YT_EVERY-1 개 이상 올라갔으면 차례. (TOP 3 는 상품 3개 기록이 글 1개)"""
    since = set()
    for d in reversed([d for d in posted if "failed" not in d]):
        if d.get("yt"):
            break
        since.add(d.get("post") or id(d))
    return len(since) >= YT_EVERY - 1


def post_youtube(posted):
    """내 채널 영상 하나를 링크 카드로 올리고, 첫 댓글에 영상 속 상품 링크를 단다. 올렸으면 True."""
    try:
        videos = json.loads(YT_LIST.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    last = {}   # 영상별 마지막으로 올린 시각
    for d in posted:
        if str(d.get("id", "")).startswith("yt:"):
            last[d["id"][3:]] = max(last.get(d["id"][3:], 0), d.get("at", 0))
    videos = [v for v in videos if v.get("products")]
    fresh = [v for v in videos if v["id"] not in last]
    if fresh:
        v = random.choice(fresh[:30])   # 안 올린 영상 중 최신 쪽에서 고른다
    else:   # 다 올렸으면 재사용: 최근 YT_REUSE_DAYS 일 안에 올린 건 빼고, 가장 오래전에 올린 것부터
        cutoff = time.time() - YT_REUSE_DAYS * 86400
        old = sorted((v for v in videos if last[v["id"]] < cutoff), key=lambda v: last[v["id"]])
        if not old:
            return False
        v = random.choice(old[:10])
    url = f"https://www.youtube.com/watch?v={v['id']}"
    tone = TONE
    body = [say(tone, "yt"), ""] + ([v["summary"]] if v.get("summary") else [])
    body += ["", say(tone, "yt_cta"), "", hashtags({"productName": v["title"]}, "리뷰영상"), "#광고"]
    text = "\n".join(body)[:MAX_TEXT]
    reply = [f'"{NOTICE}"', ""] + [f"· {n[:30]} 👉 {l}" for n, l in v["products"][:3]] + ["", say(tone, "reply")]
    reply_text = "\n".join(reply)[:MAX_TEXT]
    try:
        container = threads("/me/threads", {"media_type": "TEXT", "text": text, "link_attachment": url})
        time.sleep(30)
        post = threads("/me/threads_publish", {"creation_id": container["id"]})
    except RuntimeError as e:
        p.summary(f"### 영상 링크 글 실패 (다른 글로 대신 올림)\n- {e}")
        return False
    try:   # 본문은 이미 올라갔으니 댓글이 실패해도 같은 글을 다시 올리지 않는다
        r = threads("/me/threads", {"media_type": "TEXT", "text": reply_text, "reply_to_id": post["id"]})
        time.sleep(10)
        threads("/me/threads_publish", {"creation_id": r["id"]})
    except RuntimeError as e:
        p.summary(f"### 링크 댓글 실패 (본문은 올라감)\n- {e}")
    posted.append({"id": f"yt:{v['id']}", "at": int(time.time()), "yt": True, "tone": tone,
                   "hook": first_line(text), "post": post.get("id")})
    save_posted(posted)
    p.summary(f"## 스레드에 영상 링크 글 올림\n\n{url}\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")
    return True


def main():
    global TONE
    posted = load_posted()
    TONE = pick_tone(posted)
    USED.update(d["hook"] for d in posted if d.get("hook"))
    print("이번 말투:", TONE)
    if post_video(posted):
        return
    item, source = pick_manual(posted)   # 직접 넣은 소재(picks.txt)는 캡컷 영상 다음 1순위
    if not item:
        if yt_turn(posted) and post_youtube(posted):
            return
        if auto_turn(posted) and post_top(posted):
            return
        item, source = pick(posted)
        if item:
            item = dict(item, productUrl=short_link(item))
    if not item:
        p.summary("올릴 새 상품이 없습니다. 다음 수집 뒤에 다시 시도합니다.")
        return

    text, reply_text = compose(item, source)
    image = item.get("productImage") or ""
    card_url = coupang_card_link(item) if CARD_STYLE == "coupang" else ""
    record = {"id": str(item.get("productId")), "at": int(time.time()), "tone": TONE, "hook": first_line(text)}
    result = None
    if image and ((source != "manual" and auto_turn(posted)) or item.get("video")):
        try:
            result = publish(text, "", reply_text, card_url, auto_video(item, text))
            record["auto"] = True
        except Exception as e:   # 영상이 안 되면 평소처럼 사진 글로
            print("자동 영상 실패, 사진 글로 올립니다:", e)
            p.summary(f"### 자동 영상 실패 (사진 글로 대신 올림)\n- {e}")
    if result is None:
        result = publish(text, image, reply_text, card_url)

    record["post"] = result.get("id")
    posted.append(record)
    save_posted(posted)

    p.summary(f"## 스레드에 올림\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply_text}\n```")


if __name__ == "__main__":
    main()