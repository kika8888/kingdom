"""쇼핑 쇼츠 (예전 유튜브 쇼츠 스타일): 검은 배경 + 위쪽 상품 이름 + 가운데 상품 사진(천천히 확대)
+ 아래 큰 흰 자막(목소리에 맞춰 바뀜) + 한국어 여성 AI 목소리 + 잔잔한 배경음. 9:16, 1080x1920.

make_short(item, topic, out) → (영상 파일, 유튜브 제목, 설명란)
설명란에는 쿠팡 파트너스 링크·대가성 문구·해시태그가 들어간다.
대본은 쿠팡이 준 사실(이름·순위·할인·로켓배송)만 쓴다. 써 본 척하는 후기는 넣지 않는다.
"""
import asyncio
import random
import re
import tempfile
from pathlib import Path

import make_video as mv

W, H = 1080, 1920
PHOTO_Y, PHOTO = 420, 1080
CAP_Y = 1680   # 자막 가운데 (사진은 1500 에서 끝남)
VOICE = "ko-KR-SunHiNeural"
NOTICE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."


def script(item, topic):
    """문장 목록. 사실만 쓰고 말투는 자연스럽게 섞는다."""
    name = mv.short_name(item.get("productName", ""), 22)
    hook = random.choice([f"{topic} 찾는 분들, 이거 꼭 보세요.", f"이거 아직 모르셨어요?",
                          f"요즘 {topic} 중에 이게 제일 많이 보이더라고요.", f"이거 하나로 {topic} 고민 끝날 수도 있어요."])
    lines = [hook, f"오늘 소개할 상품은 {name}입니다."]
    rank = item.get("rank")
    if rank and topic in KNOWN_CATS:
        lines.append(f"지금 쿠팡 {topic} 베스트 {rank}위에 올라와 있는 상품이에요.")
    elif rank:
        lines.append(f"쿠팡에서 {topic} 검색하면 상위에 나오는 상품이에요.")
    if item.get("discountRate"):
        lines.append(f"게다가 지금 {int(float(item['discountRate']))}% 할인 중이에요.")
    if item.get("isRocket"):
        lines.append("로켓배송이라 주문하면 빠르게 받아볼 수 있어요.")
    elif item.get("isFreeShipping"):
        lines.append("무료배송으로 받아볼 수 있어요.")
    lines.append(random.choice(["자세한 가격과 후기는 설명란 링크에서 확인해 보세요.",
                                "궁금하신 분은 설명란 링크에서 확인해 보세요."]))
    return lines


KNOWN_CATS = {"여성패션", "남성패션", "뷰티", "출산/유아동", "식품", "주방용품", "생활용품", "홈인테리어", "가전디지털",
              "스포츠/레저", "자동차용품", "완구/취미", "문구/오피스", "헬스/건강식품", "반려동물용품"}


def speak_words(text, path):
    """목소리 파일을 만들고 [(시작초, 끝초, 단어)] 를 돌려준다."""
    import edge_tts

    async def go():
        words = []
        c = edge_tts.Communicate(text, VOICE, rate="+10%", boundary="WordBoundary")
        with open(path, "wb") as f:
            async for ch in c.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    s = ch["offset"] / 1e7
                    words.append((s, s + ch["duration"] / 1e7, ch["text"]))
        return words
    return asyncio.run(go())


def chunks(words, sentences, limit=11):
    """단어를 화면 자막 덩어리로 묶는다 (한 덩어리 ≤ limit 글자, 문장이 끝나면 끊는다)."""
    ends = set()
    pos = 0
    joined = " ".join(sentences)
    for s in sentences:   # 문장 끝 단어 위치
        pos += len(s.split())
        ends.add(pos)
    out, cur, n = [], [], 0
    for w in words:
        cur.append(w)
        n += 1
        if len("".join(x[2] for x in cur)) >= limit or n in ends:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [(c[0][0], " ".join(x[2] for x in c)) for c in out]


def frame_parts(item, tmp):
    from PIL import Image, ImageDraw
    photo = mv.photo_of(item)
    photo.resize((PHOTO * 2, PHOTO * 2)).save(tmp / "ph.png")
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    # 📌 + 상품 이름 (예전 쇼츠처럼 왼쪽 위 작은 글씨)
    d.polygon([(54, 62), (78, 62), (72, 88), (82, 98), (50, 98), (60, 88)], fill="white")
    d.line([(66, 98), (66, 118)], fill="white", width=4)
    f = mv.font(40)
    name = mv.short_name(item.get("productName", ""), 40)
    while d.textlength(name, font=f) > W - 160 and len(name) > 4:
        name = name[:-1]
    d.text((100, 90), name, font=f, fill="white", anchor="lm")
    top.save(tmp / "top.png")


def caption_png(text, path):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = mv.font(76)
    rows = mv.wrap(d, text, f, W - 120)[:2]
    y = 150 - 50 * (len(rows) - 1)
    for r in rows:
        d.text((W // 2, y), r, font=f, fill="white", anchor="mm", stroke_width=4, stroke_fill="black")
        y += 100
    img.save(path)


def make_short(item, topic, out):
    lines = script(item, topic)
    text = " ".join(lines)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        voice = tmp / "voice.mp3"
        words = speak_words(text, voice)
        total = mv.seconds(voice) + 0.8
        caps = chunks(words, lines)
        frame_parts(item, tmp)
        inputs = ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30:d={total:.2f}",
                  "-loop", "1", "-framerate", "30", "-i", str(tmp / "ph.png"),
                  "-loop", "1", "-framerate", "30", "-i", str(tmp / "top.png")]
        frames = int(total * 30) + 1
        fc = (f"[1:v]zoompan=z='1+0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:"
              f"s={PHOTO}x{PHOTO}:fps=30[p];[0:v][p]overlay=0:{PHOTO_Y}:shortest=1[a];[a][2:v]overlay=0:0:shortest=1[v0]")
        last = "v0"
        for k, (start, cap) in enumerate(caps):
            end = caps[k + 1][0] if k + 1 < len(caps) else total
            png = tmp / f"c{k}.png"
            caption_png(cap, png)
            inputs += ["-loop", "1", "-framerate", "30", "-i", str(png)]
            idx = 3 + k
            fc += f";[{last}][{idx}:v]overlay=0:{CAP_Y - 150}:shortest=1:enable='between(t,{start:.2f},{end:.2f})'[v{k + 1}]"
            last = f"v{k + 1}"
        silent = tmp / "silent.mp4"
        mv.run(inputs + ["-filter_complex", fc, "-map", f"[{last}]", "-t", f"{total:.2f}",
                         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", str(silent)])
        music = mv.bgm(tmp, total)
        mv.run(["-i", str(silent), "-i", str(voice), "-stream_loop", "-1", "-i", str(music), "-filter_complex",
                f"[1:a]apad[vo];[2:a]volume={mv.BGM_VOLUME},afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[m];"
                "[vo][m]amix=inputs=2:duration=first:normalize=0[aud]",
                "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", "-t", f"{total:.2f}", str(out)])

    name = mv.short_name(item.get("productName", ""), 40)
    title = f"{name} | {lines[0].rstrip('.')} #shorts"[:95]
    tags = ["#" + re.sub(r"[^0-9A-Za-z가-힣]", "", w) for w in ([topic] + name.split()[:3]) if len(w) >= 2]
    desc = "\n".join([lines[0], "", "👉 " + item.get("productUrl", ""), name, "", f'"{NOTICE}"', "",
                      " ".join(dict.fromkeys(tags + ["#쿠팡추천", "#shorts"]))])
    return out, title, desc


# ── TOP 5 랭킹 쇼츠 (상품 5개, 장면이 3~4초마다 바뀜) ─────────────────────

def top_script(cat, items):
    """items 는 쿠팡 순위 순(1위가 앞). 화면엔 낮은 순위부터. 순위 숫자는 쿠팡이 준 그대로."""
    lines = [random.choice([f"쿠팡 {cat} 베스트 {len(items)}개, 순위 낮은 것부터 바로 갑니다.",
                            f"요즘 쿠팡 {cat}에서 제일 잘 나가는 거 {len(items)}개 알려드릴게요.",
                            f"{cat} 뭐 살지 고민이면 이 {len(items)}개만 보세요."])]
    for it in reversed(items):
        name = mv.short_name(it.get("productName", ""), 18)
        extra = ""
        if it.get("discountRate"):
            extra = f" 지금 {int(float(it['discountRate']))}% 할인 중이에요."
        elif it.get("isRocket"):
            extra = random.choice([" 로켓배송이에요.", " 로켓배송으로 빨리 와요."])
        lines.append(f"베스트 {it.get('rank')}위, {name}.{extra}")
    lines.append("마음에 드는 거 있으면 설명란 링크에서 확인해 보세요.")
    return lines


def scene_png(item, label, badge, tmp, i):
    """장면 하나의 위쪽 글씨 + 순위 배지 (사진은 따로 움직인다)."""
    from PIL import Image, ImageDraw
    mv.photo_of(item).resize((PHOTO * 2, PHOTO * 2)).save(tmp / f"ph{i}.png")
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    d.polygon([(54, 62), (78, 62), (72, 88), (82, 98), (50, 98), (60, 88)], fill="white")
    d.line([(66, 98), (66, 118)], fill="white", width=4)
    f = mv.font(40)
    while d.textlength(label, font=f) > W - 160 and len(label) > 4:
        label = label[:-1]
    d.text((100, 90), label, font=f, fill="white", anchor="lm")
    if badge:   # 사진 왼쪽 위 금색 순위 배지
        bf = mv.font(56)
        bw = int(d.textlength(badge, font=bf)) + 60
        d.rounded_rectangle((36, PHOTO_Y + 36, 36 + bw, PHOTO_Y + 126), 45, fill=(224, 187, 69))
        d.text((36 + bw // 2, PHOTO_Y + 81), badge, font=bf, fill=(28, 31, 74), anchor="mm")
    top.save(tmp / f"top{i}.png")


def make_top_short(cat, items, out):
    """쿠팡 분야 베스트 상품 여러 개로 랭킹 쇼츠. → (영상, 제목, 설명란)"""
    lines = top_script(cat, items)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        voice = tmp / "voice.mp3"
        words = speak_words(" ".join(lines), voice)
        total = mv.seconds(voice) + 0.8
        # 문장(장면) 시작 시각: 문장마다 단어 수로 나눈다
        starts, pos = [], 0
        for s in lines:
            starts.append(words[min(pos, len(words) - 1)][0] if words else 0)
            pos += len(s.split())
        starts[0] = 0.0
        # 장면: 0 = 오프닝(1위 사진), 1..n = 낮은 순위부터, 마지막 = 마무리(1위 사진)
        order = [items[0]] + list(reversed(items)) + [items[0]]
        segs = []
        for i, it in enumerate(order):
            end = starts[i + 1] if i + 1 < len(starts) else total
            dur = max(end - starts[i], 0.5)
            label = f"쿠팡 {cat} 베스트 TOP {len(items)}" if i in (0, len(order) - 1) else mv.short_name(it.get("productName", ""), 40)
            badge = f"베스트 {it.get('rank')}위" if 0 < i < len(order) - 1 else ""
            scene_png(it, label, badge, tmp, i)
            fr = int(dur * 30) + 1
            # 펀치 줌: 처음 0.3초에 1.25배 → 1.0 으로 확 당겨진 뒤 천천히 1.06 까지
            z = f"if(lt(on,9),1.25-0.25*on/9,1+0.06*(on-9)/{max(fr - 9, 1)})"
            seg = tmp / f"s{i}.mp4"
            mv.run(["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r=30:d={dur:.3f}",
                    "-loop", "1", "-framerate", "30", "-i", str(tmp / f"ph{i}.png"),
                    "-loop", "1", "-framerate", "30", "-i", str(tmp / f"top{i}.png"),
                    "-filter_complex",
                    f"[1:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={PHOTO}x{PHOTO}:fps=30[p];"
                    f"[0:v][p]overlay=0:{PHOTO_Y}:shortest=1[a];[a][2:v]overlay=0:0:shortest=1[v]",
                    "-map", "[v]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", "-r", "30", str(seg)])
            segs.append(seg)
        (tmp / "list.txt").write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
        body = tmp / "body.mp4"
        mv.run(["-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c", "copy", str(body)])
        # 자막: 목소리에 맞춰
        caps = chunks(words, lines)
        inputs, fc, last = ["-i", str(body)], "", "0:v"
        for k, (start, cap) in enumerate(caps):
            end = caps[k + 1][0] if k + 1 < len(caps) else total
            png = tmp / f"c{k}.png"
            caption_png(cap, png)
            inputs += ["-loop", "1", "-framerate", "30", "-i", str(png)]
            fc += (";" if fc else "") + (f"[{last}][{k + 1}:v]overlay=0:{CAP_Y - 150}:shortest=1:"
                                         f"enable='between(t,{start:.2f},{end:.2f})'[v{k + 1}]")
            last = f"v{k + 1}"
        silent = tmp / "silent.mp4"
        mv.run(inputs + ["-filter_complex", fc, "-map", f"[{last}]", "-t", f"{total:.2f}",
                         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", str(silent)])
        music = mv.bgm(tmp, total)
        mv.run(["-i", str(silent), "-i", str(voice), "-stream_loop", "-1", "-i", str(music), "-filter_complex",
                f"[1:a]apad[vo];[2:a]volume={mv.BGM_VOLUME},afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[m];"
                "[vo][m]amix=inputs=2:duration=first:normalize=0[aud]",
                "-map", "0:v", "-map", "[aud]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", "-t", f"{total:.2f}", str(out)])

    title = f"쿠팡 {cat} 베스트 TOP {len(items)} | 요즘 제일 잘 나가는 거 #shorts"[:95]
    rows = [f"베스트 {it.get('rank')}위 {mv.short_name(it.get('productName', ''), 30)}\n👉 {it.get('productUrl', '')}"
            for it in reversed(items)]
    tag = "#" + re.sub(r"[^0-9A-Za-z가-힣]", "", cat)
    desc = "\n".join([lines[0], ""] + rows + ["", f'"{NOTICE}"', "", f"{tag} #쿠팡베스트 #쿠팡추천 #추천템 #shorts"])
    return out, title, desc
