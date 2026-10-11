"""매시간: 네이버 블로그 새 글을 주제별 스레드 계정에 올린다 (계정 하나 = 블로그 하나 = 주제 하나).

블로그 글은 링크 카드 + 후킹 + 제목 + 짧은 요약만 올린다 (글 전체를 옮기지 않는다).
글마다 말투·후킹·끝맺음·해시태그가 다르다 (제목에서 이름과 단어를 뽑는다).
한 번 올린 글은 다시 올리지 않고 (state/blog_threads.json), 한 번에 계정마다 1개만 올린다.
처음 연결한 계정은 지금 있는 글을 '올린 것'으로 표시해서, 그 뒤 새로 쓴 글부터 올린다.
루머성 제목(사망설·찌라시 등)은 건너뛴다 (명예훼손·허위사실 위험).

계정 추가: 아래 ACCOUNTS 에 한 줄 + 저장소 Secrets 에 그 계정 토큰 + kingdom.yml 의 blog 작업 env 에 한 줄.
"""
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
]
SKIP_WORDS = ("사망설", "찌라시", "루머", "카더라", "충격 실체", "19금")

# 후킹: 말투 5가지. {n} = 제목에서 뽑은 이름(없으면 이름 없는 문장만 쓴다). 자극적·단정적 표현은 쓰지 않는다.
HOOKS = {
    "친구": ["{n} 무슨 일이야?", "{n} 얘기 봤어?", "오늘 이 소식 다들 봤지?", "{n} 근황 정리해봄", "이거 보고 놀람"],
    "존댓말": ["{n} 소식, 정리해 드릴게요", "오늘 많이 찾아보신 소식이에요", "{n} 이야기, 무슨 일인지 짚어봤어요",
             "화제가 된 이유를 정리했어요", "{n} 관련 소식 전해 드려요"],
    "감탄": ["와 {n} 이런 일이 있었네", "이 소식 진짜 의외다", "{n} 이야기 듣고 깜짝", "이건 몰랐네", "오늘 제일 놀란 소식"],
    "질문": ["{n} 소식 들으셨어요?", "왜 이렇게 화제일까요?", "{n} 어떻게 된 일일까요?", "이 소식 어떻게 생각하세요?",
             "다들 이거 아셨어요?"],
    "짧게": ["{n} 근황", "오늘의 연예 소식", "{n} 이야기", "화제의 소식", "지금 많이 보는 뉴스"],
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
        "아들", "딸", "아내", "남편", "엄마", "아빠", "동생", "부부", "가족", "와이프", "만에", "지금은", "꼬맹이"}
VERB_END = re.compile(r"(는데|했다|한다|된다|까지|에서|으로|했나|였다|이다|라고|라며|하는|받은|받아|됐다|됐나|던|한|된|는|은|을|를|의|도)$")


def name_of(title):
    """제목에서 이름(2~4글자 한글)을 하나 뽑는다. '전 국대 골키퍼 김영광, …' → 김영광"""
    head = re.split(r"[,·:|]", title)[0].split()
    for w in reversed(head):
        w = re.sub(r"[^가-힣]", "", w)
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
        w = re.sub(r"[^A-Za-z가-힣]", "", w)
        if (len(w) >= 2 and w not in STOP and not VERB_END.search(w) and not w.endswith("서")
                and not (w.isascii() and len(w) < 3) and not any(w in q or q in w for q in picks)):
            picks.append(w)
    picks = list(dict.fromkeys(picks))[:3] + random.sample(base.split(), 2)
    return " ".join(dict.fromkeys(t if t.startswith("#") else "#" + t for t in picks))


def compose(x, acc, seen):
    """글마다 다른 말투·후킹·끝맺음·해시태그. 바로 전 글과 같은 말투, 최근 쓴 후킹은 피한다."""
    tone = random.choice([t for t in HOOKS if t != seen.get("tone")])
    n = name_of(x["title"])
    pool = [h.format(n=n) for h in HOOKS[tone] if n or "{n}" not in h]
    fresh = [h for h in pool if h not in seen.get("hooks", [])] or pool
    hook = random.choice(fresh)
    summary = x["summary"].strip()
    if summary and summary[-1] not in ".!?…다요":   # RSS 요약은 90자에서 잘려 온다
        summary = summary.rsplit(" ", 1)[0] + "…"
    lines = [hook, "", x["title"], "", summary, "", random.choice(CTA[tone]), "", tags_of(x["title"], acc["tags"])]
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


def main():
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    errors = []
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
        p.summary(f"- {acc['name']}: 토큰 확인 @{user}")
        try:
            posts = collect.naver_posts(acc["blog"])
        except Exception as e:
            errors.append(f"{acc['name']} 블로그 읽기: {e}")
            continue
        seen = state.setdefault(acc["blog"], {"posted": [], "started": False})
        if not seen["started"]:   # 처음엔 지금 있는 글은 건너뛰고, 그 뒤 새 글부터
            seen["posted"] = [x["link"] for x in posts]
            seen["started"] = True
            p.summary(f"- {acc['name']}: 처음 연결 — 지금 있는 글 {len(posts)}개는 건너뛰고 다음 새 글부터 올립니다")
            continue
        for x in posts:   # 루머성 제목은 올리지 않고 표시만
            if x["link"] not in seen["posted"] and any(w in x["title"] for w in SKIP_WORDS):
                seen["posted"].append(x["link"])
                p.summary(f"- {acc['name']}: 건너뜀(루머성 제목) {x['title']}")
        new = [x for x in posts if x["link"] not in seen["posted"]]
        if not new:
            continue
        x = new[-1]   # 가장 먼저 쓴 새 글부터 차례로 (시간당 1개)
        text = compose(x, acc, seen)
        try:
            c = post(token, {"media_type": "TEXT", "text": text, "link_attachment": x["link"]})
            time.sleep(20)
            r = post(token, {"creation_id": c["id"]})
        except RuntimeError as e:
            errors.append(f"{acc['name']} 스레드: {e}")
            continue
        seen["posted"] = (seen["posted"] + [x["link"]])[-200:]
        p.summary(f"## {acc['name']} → {acc['threads']} 올림\n\n{x['link']}\n```\n{text}\n```\n게시물 {r.get('id')}")
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    if errors:
        for e in errors:
            print(f"::error title=블로그→스레드 실패::{e[:300]}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
