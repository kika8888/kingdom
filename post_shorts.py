"""하루 3번(한국 10:30·15:30·20:30): 쿠팡 분야 베스트 TOP 5 랭킹 쇼츠를 만들어 스레드에 올린다.

영상은 shorts.make_top_short (예전 유튜브 쇼츠 스타일, 상품 5개가 펀치 줌으로 넘어감).
분야는 최근 쓴 분야를 피해서 고르고, 한 번 쓴 상품은 7일 동안 다시 쓰지 않는다 (state/shorts.json).
본문 #광고, 첫 댓글에 대가성 문구 + 순위별 링크 5개. 영상은 docs/videos 에 올려(push) 스레드에 넘긴다.
"""
import json
import random
import time
from pathlib import Path

import partners as p
import threads as t
import make_video as mv
import shorts

ROOT = Path(__file__).parent
STATE = ROOT / "state" / "shorts.json"
TOP = 5
MAX_RANK = 10   # 'TOP 5' 라고 부르니 쿠팡 베스트 10위 안 상품으로만 채운다
KEEP_DAYS = 7

HOOKS = ["요즘 {c} 제일 잘 나가는 거 5개", "{c} 뭐 살지 고민이면 이것만 보세요", "쿠팡 {c} 베스트 5개 정리했어요",
         "{c} 인기템, 순위대로 보여드릴게요", "다들 {c} 이거 사더라고요", "{c} 지금 인기 순위 한 번에 보기"]


def load():
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        st = {}
    cutoff = time.time() - KEEP_DAYS * 86400
    st["used"] = {k: v for k, v in st.get("used", {}).items() if v > cutoff}
    st.setdefault("cats", [])
    st.setdefault("hooks", [])
    return st


def pick(data, st):
    """최근 분야는 피하고, 안 쓴 상품이 5개 이상인 분야에서 쿠팡 순위 순 5개."""
    groups = []
    for cat, items in data.get("best", {}).items():
        seen, fresh = set(), []
        for i in sorted(items, key=t.rank_of):
            key = "".join(str(i.get("productName", "")).split())[:14]
            if (i.get("productImage") and i.get("productUrl") and str(i.get("productId")) not in st["used"]
                    and key not in seen and t.rank_of(i) <= MAX_RANK):
                seen.add(key)
                fresh.append(i)
        if len(fresh) >= TOP:
            groups.append((cat, fresh[:TOP]))
    if not groups:
        return None
    recent = st["cats"][-4:]
    pool = [g for g in groups if g[0] not in recent] or groups
    return random.choice(pool)


def main():
    data = json.loads((ROOT / "docs" / "products.json").read_text(encoding="utf-8"))
    st = load()
    chosen = pick(data, st)
    if not chosen:
        p.summary("쇼츠로 만들 분야가 없습니다 (상품 5개 이상인 분야 없음).")
        return
    cat, items = chosen
    items = [dict(i, productUrl=t.short_link(i)) for i in items]   # 짧은 파트너스 링크

    name = f"auto-short-{int(time.time())}.mp4"
    video = t.push_video(name, lambda out: shorts.make_top_short(cat, items, out))

    hooks = [h for h in HOOKS if h not in st["hooks"][-4:]]
    hook = random.choice(hooks).format(c=cat)
    text = "\n".join([hook, "", "순위대로 영상으로 정리했어요", "", "상품 링크는 댓글에 👇", "",
                      t.hashtags(items[0], cat), "#광고"])[:t.MAX_TEXT]
    rows = [f"{it.get('rank')}위 {mv.short_name(it.get('productName', ''), 16)} 👉 {it['productUrl']}" for it in reversed(items)]
    reply = "\n".join([f'"{t.NOTICE}"', ""] + rows)[:t.MAX_TEXT]
    result = t.publish(text, "", reply, "", video)

    now = int(time.time())
    for it in items:
        st["used"][str(it.get("productId"))] = now
    st["cats"] = (st["cats"] + [cat])[-10:]
    st["hooks"] = (st["hooks"] + [hook])[-10:]
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    p.summary(f"## TOP 5 쇼츠 올림 ({cat})\n\n{video}\n\n본문\n```\n{text}\n```\n첫 댓글\n```\n{reply}\n```\n게시물 {result.get('id')}")


if __name__ == "__main__":
    main()
