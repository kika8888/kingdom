"""3시간마다(한국 9·12·15·18·21·24시): KINGDOM 사이트 홍보 썸네일을 만들어 스레드에 올린다.

썸네일 = KINGDOM 로고 + 큰 제목 + 상품 사진 4개(할인율·순위 배지) + '전체 보기' 버튼.
주제는 골드박스 → 신기템 → 분야 베스트 순서로 돌아간다. 상품은 collect.py 가 만든 docs/products.json 에서.
본문에는 사이트 링크와 #광고 (사이트 안 상품 링크가 쿠팡 파트너스 링크라서), 첫 댓글에도 사이트 링크.
이미지는 docs/promo/ 에 올려(push) 사이트 주소로 스레드에 넘긴다.
"""
import json
import random
import subprocess
import time
from pathlib import Path

import partners as p
import threads as t

ROOT = Path(__file__).parent
SITE = "https://kingdom.papalaqi.com"
STATE = ROOT / "state" / "promo.json"
FOLDER = ROOT / "docs" / "promo"
W, H = 1080, 1350
NAVY, NAVY2, GOLD, RED, WHITE = (28, 31, 74), (46, 52, 120), (224, 187, 69), (209, 52, 43), (255, 255, 255)

HOOKS = {
    "goldbox": ["오늘 쿠팡 특가 한 페이지에 모아뒀어요", "골드박스 오늘만 이 가격이래요", "특가 찾느라 쿠팡 헤매지 마세요",
                "오늘 할인 제일 큰 것만 골랐어요", "하루만 하는 특가, 놓치기 아까운 것들"],
    "weird": ["이런 게 있었어? 신기템 모아봤어요", "요즘 뜨는 신기템 여기 다 있어요", "보자마자 갖고 싶어지는 아이디어템",
              "생활이 편해지는 신기템 모음", "매시간 새로 찾아오는 신기템"],
    "best": ["쿠팡에서 지금 제일 잘 팔리는 거", "분야별 1등만 모아봤어요", "고민될 땐 베스트부터 보세요",
             "판매 순위 그대로 정리했어요", "다들 뭐 사는지 궁금하면"],
}
CTA = ["전체 보기는 여기서 👉", "매시간 업데이트돼요 👉", "한 번에 모아 보기 👉", "저장해두고 보세요 👉"]


# ── 고르기 ────────────────────────────────────────────────────

def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"n": 0, "hooks": []}


def pick(data, theme):
    """(제목 두 줄, 부제, 상품 4개, 배지 함수)"""
    seen = set()

    def has_img(i):   # 사진 있고, 같은 상품(같은 사진 또는 이름 앞부분이 같음)은 한 번만
        u = i.get("productImage")
        name = "".join(str(i.get("productName", "")).split())[:14]
        if not u or u in seen or name in seen:
            return False
        seen.update({u, name})
        return True
    if theme == "goldbox":
        items = sorted(filter(has_img, data.get("goldbox", [])), key=lambda i: -float(i.get("discountRate") or 0))[:4]
        top = max((int(float(i.get("discountRate") or 0)) for i in items), default=0)
        title = ["오늘의 골드박스", f"최대 {top}% 할인" if top else "하루 특가 모음"]
        return title, "하루만 이 가격 · 매시간 업데이트", items, lambda i: f"-{int(float(i['discountRate']))}%" if i.get("discountRate") else "특가"
    if theme == "weird":
        groups = [(k, [i for i in v if has_img(i)]) for k, v in data.get("keywords", {}).items()]
        groups = [g for g in groups if len(g[1]) >= 4]
        if not groups:
            return None
        kw, items = random.choice(groups)
        return ["요즘 뜨는", kw], "이런 게 있었어? 신기템 모음", items[:4], lambda i: "신기템"
    groups = [(k, sorted(filter(has_img, v), key=t.rank_of)) for k, v in data.get("best", {}).items()]
    groups = [g for g in groups if len(g[1]) >= 4]
    if not groups:
        return None
    cat, items = random.choice(groups)
    return [f"쿠팡 {cat}", "베스트 TOP 4"], "판매 순위 그대로 · 매시간 업데이트", items[:4], lambda i: f"BEST {t.rank_of(i)}"


# ── 썸네일 ───────────────────────────────────────────────────

def thumbnail(title, sub, items, badge, out):
    from PIL import Image, ImageDraw
    import make_video as mv
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):   # 위→아래 남색 그라데이션
        r = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * r) for a, b in zip(NAVY, NAVY2)))

    # 로고: 왕관 + KINGDOM
    cx = 70
    d.polygon([(cx, 108), (cx + 14, 72), (cx + 32, 96), (cx + 50, 64), (cx + 68, 96), (cx + 86, 72), (cx + 100, 108)], fill=GOLD)
    d.rectangle([cx, 112, cx + 100, 122], fill=GOLD)
    d.text((cx + 120, 95), "KINGDOM", font=mv.font(54), fill=WHITE, anchor="lm")

    # 제목 두 줄 (둘째 줄 금색)
    d.text((70, 205), title[0], font=mv.font(86), fill=WHITE, anchor="lm")
    big = mv.font(98)
    line2 = title[1]
    while d.textlength(line2, font=big) > W - 140 and len(line2) > 4:
        line2 = line2[:-1]
    d.text((70, 308), line2, font=big, fill=GOLD, anchor="lm")
    d.text((72, 390), sub, font=mv.font(38), fill=(201, 203, 224), anchor="lm")

    # 상품 2x2 카드
    size, gap, top = 398, 22, 438
    left = (W - 2 * size - gap) // 2
    for k, it in enumerate(items[:4]):
        x = left + (k % 2) * (size + gap)
        y = top + (k // 2) * (size + gap)
        card = Image.new("RGB", (size, size), WHITE)
        try:
            ph = mv.photo_of(it).resize((size, size))
            card.paste(ph, (0, 0))
        except Exception:
            pass
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), 36, fill=255)
        img.paste(card, (x, y), mask)
        b = badge(it)
        bf = mv.font(40)
        bw = int(d.textlength(b, font=bf)) + 36
        d.rounded_rectangle((x + 16, y + 16, x + 16 + bw, y + 76), 18, fill=RED if b.startswith("-") else GOLD)
        d.text((x + 16 + bw // 2, y + 46), b, font=bf, fill=WHITE if b.startswith("-") else NAVY, anchor="mm")

    # 아래 버튼
    by = top + 2 * size + gap + 22   # 1278
    d.rounded_rectangle((left, by, W - left, by + 58), 29, fill=GOLD)
    d.text((W // 2, by + 29), "전체 보기  →  kingdom.papalaqi.com", font=mv.font(36), fill=NAVY, anchor="mm")
    img.save(out, quality=90)
    return out


def push_image(build, name):
    """docs/promo 에 이미지를 올리고(push) 사이트에 반영되면 주소를 돌려준다."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    for old in FOLDER.glob("promo-*.jpg"):   # 지난 이미지는 스레드가 이미 가져갔다
        old.unlink()
    build(FOLDER / name)
    git = ["git", "-c", "user.name=kingdom-bot", "-c", "user.email=kingdom-bot@users.noreply.github.com"]
    for cmd in (["add", "-A", "docs/promo"], ["commit", "-m", "promo image"], ["pull", "--rebase"], ["push"]):
        r = subprocess.run(git + cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {cmd[0]} 실패: {(r.stderr or r.stdout).strip()[:200]}")
    url = f"{SITE}/promo/{name}"
    for _ in range(24):   # 사이트 반영 최대 6분
        time.sleep(15)
        if t.online(url):
            return url
    raise RuntimeError("홍보 이미지가 사이트에 반영되지 않았습니다")


def main():
    data = json.loads((ROOT / "docs" / "products.json").read_text(encoding="utf-8"))
    st = load_state()
    themes = ["goldbox", "weird", "best"]
    chosen = None
    for k in range(3):   # 차례인 주제가 비어 있으면 다음 주제
        theme = themes[(st["n"] + k) % 3]
        chosen = pick(data, theme)
        if chosen:
            break
    if not chosen:
        p.summary("홍보할 상품이 없습니다.")
        return
    title, sub, items, badge = chosen
    hooks = [h for h in HOOKS[theme] if h not in st["hooks"][-6:]] or HOOKS[theme]
    hook = random.choice(hooks)
    text = "\n".join([hook, "", f"{' '.join(title)} — {sub}", "", random.choice(CTA), SITE, "",
                      "#쿠팡특가 #신기템 #골드박스 #쇼핑정보 #KINGDOM", "#광고"])
    reply = f'"{t.NOTICE}"\n\n전체 상품 보기 👉 {SITE}'
    name = f"promo-{int(time.time())}.jpg"
    image = push_image(lambda out: thumbnail(title, sub, items, badge, out), name)
    result = t.publish(text, image, reply)

    st["n"] = (themes.index(theme) + 1)
    st["hooks"] = (st["hooks"] + [hook])[-20:]
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    p.summary(f"## KINGDOM 홍보 글 올림 ({theme})\n\n{image}\n\n```\n{text}\n```\n게시물 {result.get('id')}")


if __name__ == "__main__":
    main()
