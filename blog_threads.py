"""매시간: 네이버 블로그 새 글을 주제별 스레드 계정에 올린다 (계정 하나 = 블로그 하나 = 주제 하나).

블로그 글은 링크 카드 + 후킹 + 제목 + 짧은 요약만 올린다 (글 전체를 옮기지 않는다).
글마다 말투·후킹·끝맺음·해시태그가 다르다 (제목에서 이름과 단어를 뽑는다).
새 글은 매시간 확인해서 바로 올리고, 새 글이 없을 땐 전에 쓴 글을 3시간에 1개씩(최근 글부터) 올린다.
한 번 올린 글은 다시 올리지 않고 (state/blog_threads.json), 한 번 실행에 계정마다 1개만 올린다.
루머성 제목(사망설·찌라시 등)은 건너뛴다 (명예훼손·허위사실 위험).

계정 추가: 아래 ACCOUNTS 에 한 줄 + 저장소 Secrets 에 그 계정 토큰 + kingdom.yml 의 blog 작업 env 에 한 줄.
"""
import html
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import collect
import partners as p

ROOT = Path(__file__).parent
STATE = ROOT / "state" / "blog_threads.json"
API = "https://graph.threads.net/v1.0"

ACCOUNTS = [
    {"name": "연예", "blog": "soduwk1209", "token": "THREADS_TOKEN_ENT", "threads": "@yesol276",
     "tags": "#연예뉴스 #연예 #스타 #방송 #이슈"},
    {"name": "스포츠", "blog": "dkdk521", "token": "THREADS_TOKEN_SPORTS", "threads": "@pantaqi9988",
     "tags": "#스포츠뉴스 #스포츠 #경기 #하이라이트 #이슈"},
]
SKIP_WORDS = ("사망설", "찌라시", "루머", "카더라", "충격 실체", "19금")

# 후킹: 말투 5가지. {n} = 제목에서 뽑은 이름(없으면 이름 없는 문장만 쓴다), {t} = 주제(연예·스포츠).
# 자극적·단정적 표현은 쓰지 않는다.
HOOKS = {
    "친구": ["{n} 무슨 일이야?", "{n} 얘기 봤어?", "오늘 이 소식 다들 봤지?", "{n} 근황 정리해봄", "이거 보고 놀람"],
    "존댓말": ["{n} 소식, 정리해 드릴게요", "오늘 많이 찾아보신 소식이에요", "{n} 이야기, 무슨 일인지 짚어봤어요",
             "화제가 된 이유를 정리했어요", "{n} 관련 소식 전해 드려요"],
    "감탄": ["와 {n} 이런 일이 있었네", "이 소식 진짜 의외다", "{n} 이야기 듣고 깜짝", "이건 몰랐네", "오늘 제일 놀란 소식"],
    "질문": ["{n} 소식 들으셨어요?", "왜 이렇게 화제일까요?", "{n} 어떻게 된 일일까요?", "이 소식 어떻게 생각하세요?",
             "다들 이거 아셨어요?"],
    "짧게": ["{n} 근황", "오늘의 {t} 소식", "{n} 이야기", "화제의 소식", "지금 많이 보는 {t} 뉴스"],
}
CTA = {
    "친구": ["자세한 건 블로그에 정리해놨어 👇", "전체 내용은 여기 👇"],
    "존댓말": ["자세한 내용은 블로그에서 확인하세요 👇", "전체 내용은 아래 링크에 있어요 👇"],
    "감탄": ["자세한 이야기는 여기서 👇", "전체 내용 보러 가기 👇"],
    "질문": ["자세한 내용 궁금하시면 👇", "어떻게 된 건지 링크에서 확인해 보세요 👇"],
    "짧게": ["더 보기 👇", "전문 👇"],
}
STOP = {"결국", "이유", "그리고", "하지만", "근황", "공개", "포착", "이후", "모습", "사실", "충격", "논란", "화제", "드디어",
        "숙인", "고개", "무슨", "일이", "공식", "입장", "국대", "출신", "정말", "진짜", "모두", "다시", "역대", "최근",
        "아들", "딸", "아내", "남편", "엄마", "아빠", "동생", "부부", "가족", "와이프", "만에", "지금은", "꼬맹이",
        "겨우", "결국", "리더보드", "디펜딩", "챔피언", "총정리", "마지막", "무대", "중계", "자격", "상실", "도전", "반전"}
VERB_END = re.compile(r"(는데|까지|에서|으로|했나|라고|라며|하는|받은|받아|됐나|다|던|한|된|는|은|을|를|의|도|긴|게|고)$")


SURNAMES = set("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구민진나지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모탁국어은편용예봉경사부가복태목형피두감음빈동온호범좌팽승간상갈")


def name_of(title):
    """제목에서 사람 이름을 하나 뽑는다. 3글자 한글을 먼저(박성현·김효주), 없으면 앞부분의 2~4글자.
    숫자가 섞인 말(2위→13위)·동사·흔한 말은 뺀다."""
    words = [w for w in re.split(r"[\s,·:|…'‘’\"“”]+", title) if w and not re.search(r"\d", w)]
    words = [re.sub(r"[^가-힣]", "", w) for w in words]
    ok = [w for w in words if w and w not in STOP and not VERB_END.search(w)]
    three = [w for w in ok if len(w) == 3 and w[0] in SURNAMES and not re.search(r"(에|만|와|과|랑)$", w)]
    if three:
        return three[0]
    head = [re.sub(r"[^가-힣]", "", w) for w in re.split(r"[,·:|…]", title)[0].split() if not re.search(r"\d", w)]
    for w in reversed(head):
        if 2 <= len(w) <= 4 and w not in STOP and not VERB_END.search(w):
            return w
    return ""


def tags_of(title, base):
    """이름 → 따옴표 속 프로그램 이름 → 나머지 명사 순으로 3개 + 기본 태그 2개."""
    picks = []
    n = name_of(title)
    if n:
        picks.append(n)
    for q in re.findall(r"['‘’\"“”]([^'‘’\"“”]{2,15})['‘’\"“”]", title):   # '아는 와이프' → 아는와이프
        q = re.sub(r"[^0-9A-Za-z가-힣]", "", q)
        if len(q) >= 2 and "사망" not in q:
            picks.append(q)
    for w in re.split(r"[\s,·:|'‘’\"“”…]+", title):
        if re.search(r"\d", w):   # 2위→13위, 49대11로 같은 숫자 섞인 말은 태그로 쓰지 않는다
            continue
        w = re.sub(r"[^A-Za-z가-힣]", "", w)
        if (len(w) >= 2 and w not in STOP and not VERB_END.search(w) and not re.search(r"(서|에|만|와|과|랑|히|온)$", w)
                and not (w.isascii() and len(w) < 3) and not any(w in q or q in w for q in picks)):
            picks.append(w)
    picks = list(dict.fromkeys(picks))[:3] + random.sample(base.split(), 2)
    return " ".join(dict.fromkeys(t if t.startswith("#") else "#" + t for t in picks))


def compose(x, acc, seen):
    """글마다 다른 말투·후킹·끝맺음·해시태그. 바로 전 글과 같은 말투, 최근 쓴 후킹은 피한다."""
    tone = random.choice([t for t in HOOKS if t != seen.get("tone")])
    n = name_of(x["title"])
    if not (len(n) == 3 and n[0] in SURNAMES):   # '노래방 무슨 일이야?' 같은 어색한 후킹 방지: 사람 이름일 때만 넣는다
        n = ""
    pool =[h.format(n=n, t=acc["name"]) for h in HOOKS[tone] if n or "{n}" not in h]
    fresh = [h for h in pool if h not in seen.get("hooks", [])] or pool
    hook = random.choice(fresh)
    summary = x["summary"].strip()
    if summary and summary[-1] not in ".!?…다요":   # RSS 요약은 90자에서 잘려 온다
        summary = summary.rsplit(" ", 1)[0] + "…"
    # 스레드는 글 하나에 주제 태그 1개만 인식하고 나머지 #단어 는 글자로 남아 지저분해진다 → 태그는 1개만.
    # 제목은 아래 링크 카드에 이미 나오므로 본문에 다시 쓰지 않는다.
    real_name = n if len(n) == 3 and n[0] in SURNAMES else ""
    tag = "#" + (real_name or acc["tags"].split()[0].lstrip("#"))
    lines = [hook, "", summary, "", random.choice(CTA[tone]) + " " + tag]
    seen["tone"] = tone
    seen["hooks"] = (seen.get("hooks", []) + [hook])[-15:]
    return "\n".join(lines)[:500]


def post(token, params):
    path = "/me/threads_publish" if "creation_id" in params else "/me/threads"
    req = urllib.request.Request(f"{API}{path}", data=urllib.parse.urlencode(dict(params, access_token=token)).encode(),
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"스레드 API 오류 {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None


def whoami(token):
    """토큰 주인 계정 아이디. 다른 계정 토큰이 들어가 있으면 주제가 섞이므로 올리기 전에 확인한다."""
    q = urllib.parse.urlencode({"fields": "username", "access_token": token})
    try:
        with urllib.request.urlopen(f"{API}/me?{q}", timeout=30) as res:
            return json.loads(res.read().decode("utf-8")).get("username", "")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"토큰 확인 실패 {e.code}: {e.read().decode('utf-8', 'replace')[:200]}") from None


NEW_EVERY_H = 1    # 새 글: 매시간 확인해서 바로
OLD_EVERY_H = 3    # 전에 쓴 글: 새 글이 없을 때 3시간에 1개씩, 최근 글부터 거꾸로
SKIP_PREFIX = ("[공유]",)   # 남의 글 공유 등은 올리지 않는다


def blog_list(blog):
    """블로그 전체 글 [(링크, 제목)] — 최신 글이 앞."""
    out, seen, page = [], set(), 1
    while page <= 100:
        u = (f"https://blog.naver.com/PostTitleListAsync.naver?blogId={blog}&currentPage={page}"
             f"&categoryNo=0&parentCategoryNo=0&countPerPage=30")
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as res:
            t = res.read().decode("utf-8")
        rows = [(n, html.unescape(urllib.parse.unquote_plus(ti)))
                for n, ti in re.findall(r'"logNo":"(\d+)","title":"([^"]*)"', t)]
        rows = [r for r in rows if r[0] not in seen]
        if not rows:
            break
        for n, ti in rows:
            seen.add(n)
            out.append((f"https://blog.naver.com/{blog}/{n}", ti))
        page += 1
        time.sleep(0.3)
    return out


def post_meta(link):
    """글 하나의 제목·요약 (모바일 페이지의 og 태그)."""
    blog, no = link.rstrip("/").split("/")[-2:]
    u = f"https://m.blog.naver.com/{blog}/{no}"
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as res:
        t = res.read().decode("utf-8", "replace")
    get = lambda k: html.unescape((re.search(rf'<meta property="og:{k}" content="([^"]*)"', t) or [None, ""])[1]).strip()
    return {"link": link, "title": get("title"), "summary": get("description").rstrip(".")}


def skip(title):
    return any(w in title for w in SKIP_WORDS) or title.startswith(SKIP_PREFIX)


def publish(token, acc, x, seen):
    """본문은 링크 없이(스레드는 링크 없는 글을 더 퍼뜨린다), 링크 카드는 첫 댓글로.
    댓글 권한이 없으면 예전처럼 본문에 링크를 붙이고, 다음부터는 계속 그 방식으로 올린다."""
    text = compose(x, acc, seen)
    if seen.get("reply_ok") is False:
        c = post(token, {"media_type": "TEXT", "text": text, "link_attachment": x["link"]})
        time.sleep(20)
        r = post(token, {"creation_id": c["id"]})
    else:
        body = text.replace("👇", "👇 (첫 댓글에 링크)", 1)
        c = post(token, {"media_type": "TEXT", "text": body})
        time.sleep(20)
        r = post(token, {"creation_id": c["id"]})
        try:
            time.sleep(10)
            c2 = post(token, {"media_type": "TEXT", "text": f"전체 내용 👉 {x['title'][:80]}",
                              "link_attachment": x["link"], "reply_to_id": r["id"]})
            time.sleep(20)
            post(token, {"creation_id": c2["id"]})
            seen["reply_ok"] = True
            text = body
        except RuntimeError as e:
            print(f"::warning title=첫 댓글 실패, 본문 링크 방식으로 바꿉니다::{e}")
            seen["reply_ok"] = False
            c = post(token, {"media_type": "TEXT", "text": text, "link_attachment": x["link"]})
            time.sleep(20)
            r = post(token, {"creation_id": c["id"]})
    seen["posted"].append(x["link"])
    return text, r


def main():
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    errors = []
    now = time.time()
    for acc in ACCOUNTS:
        token = os.environ.get(acc["token"], "").strip()
        if not token:
            print(f"{acc['name']}: {acc['token']} 가 없어 건너뜀")
            continue
        try:
            user = whoami(token)
        except RuntimeError as e:
            errors.append(f"{acc['name']}: {e}")
            continue
        if "@" + user != acc["threads"]:
            errors.append(f"{acc['name']}: 토큰이 {acc['threads']} 가 아니라 @{user} 계정 것이라 올리지 않았습니다")
            continue
        seen = state.setdefault(acc["blog"], {})
        if seen.get("v") != 2:   # 처음(또는 예전 방식): 지금 있는 글 전체를 '전에 쓴 글' 목록으로
            try:
                old = blog_list(acc["blog"])
            except Exception as e:
                errors.append(f"{acc['name']} 블로그 목록: {e}")
                continue
            seen.update({"v": 2, "posted": [], "known": [l for l, t in old],
                         "backlog": [l for l, t in old if not skip(t)], "last_old": 0})
            p.summary(f"- {acc['name']}: 전에 쓴 글 {len(seen['backlog'])}개를 3시간에 1개씩 올릴 목록에 넣었습니다")
        try:
            rss = collect.naver_posts(acc["blog"])
        except Exception as e:
            errors.append(f"{acc['name']} 블로그 읽기: {e}")
            continue
        # 1) 새 글: 처음 연결 뒤에 새로 쓴 글이 있으면 바로 (가장 먼저 쓴 것부터 1개)
        new = [x for x in rss if x["link"] not in seen["known"]]
        for x in new:
            seen["known"].append(x["link"])
            if skip(x["title"]):
                p.summary(f"- {acc['name']}: 건너뜀(루머성·공유 글) {x['title']}")
            elif x["link"] not in seen["posted"]:
                seen.setdefault("queue", []).append(x["link"])
        try:
            if seen.get("queue"):
                link = seen["queue"].pop(0)
                x = next((r for r in rss if r["link"] == link), None) or post_meta(link)
                kind = "새 글"
            elif seen["backlog"] and now - seen["last_old"] >= OLD_EVERY_H * 3600 - 300:
                seen["backlog"] = [l for l in seen["backlog"] if l not in seen["posted"]]
                x = post_meta(seen["backlog"].pop(0))
                seen["last_old"] = now
                kind = "전에 쓴 글"
            else:
                continue
            text, r = publish(token, acc, x, seen)
        except Exception as e:
            errors.append(f"{acc['name']} 스레드: {e}")
            continue
        p.summary(f"## {acc['name']} → {acc['threads']} {kind} 올림 (남은 전에 쓴 글 {len(seen['backlog'])}개)\n\n"
                  f"{x['link']}\n```\n{text}\n```\n게시물 {r.get('id')}")
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    if errors:
        for e in errors:
            print(f"::error title=블로그→스레드 실패::{e[:300]}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
