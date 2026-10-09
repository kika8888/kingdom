"""자동 상품 영상: 큰 글씨 장면 + 한국어 여성 AI 목소리 + 잔잔한 배경음. 사진은 천천히 확대된다.

  make_top(): 상품 3개 랭킹 영상 (오프닝 → 낮은 순위부터 → 마무리, 장면마다 다른 사진)
  make():     상품 1개 영상 (3개가 안 모일 때)

threads.py 가 글 3개 중 1개를 이 영상으로 올린다. 만들기에 실패하면 사진 글로 올린다.
필요한 것 (kingdom.yml 의 threads 작업에서 설치): pillow, edge-tts, gTTS, imageio-ffmpeg, fonts-noto-cjk

배경음: bgm/ 폴더에 mp3 를 넣으면 그중 하나를 무작위로 쓴다 (저작권 없는 무료 음원만!).
비어 있으면 직접 만든 잔잔한 멜로디를 쓴다.
"""
import array
import asyncio
import io
import math
import random
import re
import subprocess
import tempfile
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).parent
BGM_DIR = ROOT / "bgm"
VOICE = "ko-KR-SunHiNeural"   # 한국어 여성 목소리
W, H = 1080, 1920
PIC, PIC_X, PIC_Y = 880, 100, 600   # 상품 사진 자리
BGM_VOLUME = 0.18             # 목소리 대비 배경음 크기
FONTS = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "C:/Windows/Fonts/malgunbd.ttf"]


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args):
    r = subprocess.run([ffmpeg(), "-y", "-loglevel", "error"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("ffmpeg 오류: " + r.stderr.strip()[-300:])


def seconds(path):
    r = subprocess.run([ffmpeg(), "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 3.0


def plain(text):
    """이모지 등 글꼴·목소리가 못 읽는 글자를 뺀다."""
    return re.sub(r"[^\u0000-\uFFFF]|[\u2600-\u27BF\uFE0F]", "", str(text)).strip()


def short_name(name, limit=24):
    """화면·목소리용 짧은 상품 이름: 쉼표 앞, [괄호] 빼고, 너무 길면 자른다."""
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", str(name).split(",")[0]).strip()
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0]
    return plain(s)


def photo_of(item):
    from PIL import Image
    with urllib.request.urlopen(item["productImage"], timeout=30) as res:
        return Image.open(io.BytesIO(res.read())).convert("RGB")


def collage(photos):
    """사진 2~3장을 한 장(정사각형)으로 모은다."""
    from PIL import Image
    c = Image.new("RGB", (PIC, PIC), "white")
    half = PIC // 2 - 6
    spots = [(0, 0), (PIC - half, 0), ((PIC - half) // 2, PIC - half)]
    for ph, xy in zip(photos[:3], spots):
        c.paste(ph.resize((half, half)), xy)
    return c


# ── 그림 ─────────────────────────────────────────────────────

def font(size):
    from PIL import ImageFont
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size, index=1) if f.endswith(".ttc") else ImageFont.truetype(f, size)
    raise RuntimeError("한글 글꼴이 없습니다 (fonts-noto-cjk 설치 필요)")


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=fnt) > width and line:
            cut = line.rfind(" ")
            if cut > 0:
                lines.append(line[:cut])
                line = line[cut + 1:]
            else:
                lines.append(line)
                line = ""
        line += ch
    return lines + [line] if line else lines


def layers(photo, title, lines, tmp, i):
    """배경(흐린 사진), 사진, 글씨(투명 바탕) 세 장. 사진만 따로 움직이게 나눈다."""
    from PIL import Image, ImageDraw, ImageFilter
    bg = photo.resize((H, H)).crop(((H - W) // 2, 0, (H - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), "black"), 0.45)
    bg.save(tmp / f"bg{i}.png")
    photo.resize((PIC * 2, PIC * 2)).save(tmp / f"ph{i}.png")   # 확대해도 깨지지 않게 크게

    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    big = font(84)
    y = 200
    for ln in wrap(d, title, big, W - 140)[:3]:
        d.text((W // 2, y), ln, font=big, fill="white", anchor="mm", stroke_width=6, stroke_fill="black")
        y += 110
    mid = font(54)
    rows = [x for t in lines for x in wrap(d, t, mid, W - 160)][:4]
    y = 1610 - 50 * (len(rows) - 1)   # 줄 수에 맞춰 위로 올린다
    for ln in rows:
        d.rounded_rectangle((60, y - 44, W - 60, y + 44), 22, fill=(255, 214, 0))
        d.text((W // 2, y), ln, font=mid, fill="black", anchor="mm")
        y += 100
    top.save(tmp / f"tx{i}.png")

    mask = Image.new("L", (PIC, PIC), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PIC, PIC), 48, fill=255)
    mask.save(tmp / "mask.png")


def scene(photo, title, lines, say, tmp, i, zoom_in=True):
    """장면 하나 = 사진이 천천히 확대(또는 축소)되는 영상 + 목소리."""
    layers(photo, title, lines, tmp, i)
    mp3 = tmp / f"s{i}.mp3"
    speak(plain(say), mp3)
    secs = seconds(mp3) + 0.6
    frames = int(secs * 30) + 1
    z = f"1+0.16*on/{frames}" if zoom_in else f"1.16-0.16*on/{frames}"
    seg = tmp / f"s{i}.mp4"
    run(["-loop", "1", "-framerate", "30", "-i", str(tmp / f"bg{i}.png"),
         "-loop", "1", "-framerate", "30", "-i", str(tmp / f"ph{i}.png"),
         "-loop", "1", "-framerate", "30", "-i", str(tmp / f"tx{i}.png"),
         "-loop", "1", "-framerate", "30", "-i", str(tmp / "mask.png"),
         "-i", str(mp3),
         "-filter_complex",
         f"[1:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={PIC}x{PIC}:fps=30,format=rgba[p];"
         f"[3:v]format=gray[m];[p][m]alphamerge[pm];"
         f"[0:v][pm]overlay={PIC_X}:{PIC_Y}[b];[b][2:v]overlay=0:0,format=yuv420p[v]",
         "-map", "[v]", "-map", "4:a", "-af", "apad=pad_dur=0.6",
         "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-c:a", "aac", "-ar", "44100", "-ac", "2",
         "-t", f"{secs:.2f}", str(seg)])
    return seg


# ── 소리 ─────────────────────────────────────────────────────

def speak(text, path):
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE, rate="+8%").save(str(path)))
        if path.stat().st_size > 1000:
            return
    except Exception as e:
        print("edge-tts 실패, gTTS 로 대신:", e)
    from gtts import gTTS
    gTTS(text, lang="ko").save(str(path))


def melody(path, secs):
    """저작권 걱정 없는 잔잔한 배경 멜로디 (C-G-Am-F 아르페지오 + 은은한 화음)."""
    rate, bpm = 22050, 96
    beat = 60 / bpm / 2
    chords = [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]]
    n = int(secs * rate) + rate
    out = [0.0] * n
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    step = 0
    t0 = 0.0
    while t0 < secs + 1:
        chord = chords[(step // 8) % 4]
        note = chord[[0, 1, 2, 3, 2, 1, 2, 3][step % 8]] + 12
        start, length = int(t0 * rate), int(beat * 3 * rate)
        for i in range(length):
            if start + i >= n:
                break
            t = i / rate
            out[start + i] += 0.22 * math.exp(-t * 3.2) * (math.sin(2 * math.pi * hz(note) * t)
                                                           + 0.3 * math.sin(4 * math.pi * hz(note) * t))
        if step % 8 == 0:   # 화음 깔기
            for m in chord[:3]:
                for i in range(int(beat * 8 * rate)):
                    if start + i >= n:
                        break
                    t = i / rate
                    out[start + i] += 0.05 * min(1, t * 4) * math.exp(-t * 0.6) * math.sin(2 * math.pi * hz(m - 12) * t)
        step += 1
        t0 += beat
    peak = max(abs(x) for x in out) or 1
    pcm = array.array("h", (int(x / peak * 26000) for x in out))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def bgm(tmp, secs):
    files = sorted(BGM_DIR.glob("*.mp3")) + sorted(BGM_DIR.glob("*.m4a")) if BGM_DIR.exists() else []
    if files:
        return random.choice(files)
    path = tmp / "bgm.wav"
    melody(path, secs)
    return path


# ── 영상 ─────────────────────────────────────────────────────

def finish(segs, tmp, out):
    """장면들을 이어 붙이고 배경음을 깐다."""
    (tmp / "list.txt").write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    voice = tmp / "voice.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c", "copy", str(voice)])
    total = seconds(voice)
    music = bgm(tmp, total)
    run(["-i", str(voice), "-stream_loop", "-1", "-i", str(music), "-filter_complex",
         f"[1:a]volume={BGM_VOLUME},afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[m];"
         "[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", "-t", f"{total:.2f}", str(out)])
    return out


def facts_of(item):
    out = []
    if item.get("discountRate"):
        out.append(f"{item['discountRate']}% 할인 중")
    if item.get("isRocket"):
        out.append("로켓배송")
    elif item.get("isFreeShipping"):
        out.append("무료배송")
    return out


def make_top(title, items, labels, out):
    """상품 여러 개 랭킹 영상. items 는 인기순, labels 는 실제 순위 글씨(예: "베스트 2위").
    순위는 쿠팡이 준 숫자 그대로 쓴다 (걸러진 상품 때문에 2·3·5위처럼 띄엄띄엄일 수 있음).
    화면엔 낮은 순위부터 나온다."""
    photos = [photo_of(i) for i in items]
    names = [short_name(i.get("productName", "")) for i in items]
    title = plain(title)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        segs = [scene(collage(photos), title, [f"인기 상품 {len(items)}개"],
                      f"{title}. 인기 상품 {len(items)}개 바로 알려드릴게요", tmp, 0)]
        for k in range(len(items) - 1, -1, -1):
            item, name, label = items[k], names[k], plain(labels[k])
            facts = facts_of(item)
            say = f"{label}. {name}." + (" " + ", ".join(facts) + "." if facts else "")
            segs.append(scene(photos[k], label, [name] + ([" · ".join(facts)] if facts else []),
                              say, tmp, len(segs), zoom_in=k % 2 == 0))
        segs.append(scene(collage(photos), "마음에 드는 거 있었나요?", ["링크는 댓글에서 확인"],
                          "마음에 드는 거 있으면 댓글 링크에서 확인해 보세요", tmp, len(segs), zoom_in=False))
        return finish(segs, tmp, out)


def make(item, hook, facts, out):
    """상품 1개 영상 (3개가 안 모일 때). 같은 사진이 확대 → 축소 → 확대로 움직인다."""
    photo = photo_of(item)
    hook = plain(hook)
    facts = [plain(f) for f in facts if "사진 보면" not in f] or ["요즘 많이 찾는 상품이에요"]
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        segs = [scene(photo, hook, [], hook, tmp, 0),
                scene(photo, hook, facts[:2], ". ".join(facts[:2]), tmp, 1, zoom_in=False),
                scene(photo, hook, ["자세한 정보는 댓글 링크에서"], "자세한 정보는 댓글 링크에서 확인해 보세요", tmp, 2)]
        return finish(segs, tmp, out)
