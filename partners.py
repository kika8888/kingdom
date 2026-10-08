"""쿠팡 파트너스 Open API 공통 모듈 (표준 라이브러리만 사용)

키는 코드에 적지 않는다. GitHub 저장소 Settings > Secrets 에 넣으면
Actions 가 환경변수로 넘겨준다.
  COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY   (필수)
  PARTNERS_SUB_ID                          (선택: 채널 구분용)
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID     (선택: 알림용)
"""
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

DOMAIN = "https://api-gateway.coupang.com"
BASE = "/v2/providers/affiliate_open_api/apis/openapi/v1"
KST = timezone(timedelta(hours=9))


def _keys():
    ak = os.environ.get("COUPANG_ACCESS_KEY", "").strip()
    sk = os.environ.get("COUPANG_SECRET_KEY", "").strip()
    if not ak or not sk:
        raise SystemExit("COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 가 설정되지 않았습니다. "
                         "저장소 Settings > Secrets and variables > Actions 에 넣어 주세요.")
    return ak, sk


def _authorization(method, url, ak, sk):
    """쿠팡 공식 예제와 같은 HMAC-SHA256 서명. 서명 시각은 GMT 기준."""
    path, _, query = url.partition("?")
    signed_date = time.strftime("%y%m%d", time.gmtime()) + "T" + time.strftime("%H%M%S", time.gmtime()) + "Z"
    message = signed_date + method + path + query
    signature = hmac.new(sk.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ak}, signed-date={signed_date}, signature={signature}"


def call(method, path, params=None, body=None):
    """path 는 BASE 뒤쪽 경로. 응답의 data 부분을 돌려준다."""
    ak, sk = _keys()
    url = BASE + path
    if params:
        params = {k: v for k, v in params.items() if v not in (None, "")}
        if params:
            url += "?" + urllib.parse.urlencode(params)

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(DOMAIN + url, data=data, method=method)
    req.add_header("Authorization", _authorization(method, url, ak, sk))
    req.add_header("Content-Type", "application/json;charset=UTF-8")

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"쿠팡 API 오류 {e.code} ({path}): {detail}") from None

    if str(payload.get("rCode", "0")) != "0":
        raise RuntimeError(f"쿠팡 API 오류 ({path}): {payload.get('rMessage')}")
    return payload.get("data")


def sub_id():
    return os.environ.get("PARTNERS_SUB_ID", "").strip() or None


# ── 기능별 함수 ─────────────────────────────────────────────

def goldbox():
    return call("GET", "/products/goldbox", {"subId": sub_id(), "imageSize": "512x512"}) or []


BEST_CATEGORIES = {
    "1001": "여성패션", "1002": "남성패션", "1010": "뷰티", "1011": "출산/유아동", "1012": "식품",
    "1013": "주방용품", "1014": "생활용품", "1015": "홈인테리어", "1016": "가전디지털",
    "1017": "스포츠/레저", "1018": "자동차용품", "1020": "완구/취미", "1021": "문구/오피스",
    "1024": "헬스/건강식품", "1029": "반려동물용품",
}


# 쿠팡 베스트는 다른 분야 상품을 섞어 준다 (남성패션에 생수, 헬스/건강식품에 애호박 등).
# 상품마다 붙어 오는 categoryName 이 이 목록에 있는 것만 남긴다.
BEST_MATCH = {
    "1001": {"패션의류", "패션잡화"}, "1002": {"패션의류", "패션잡화"}, "1010": {"뷰티"},
    "1011": {"출산/유아"}, "1012": {"식품", "로켓프레시"}, "1013": {"주방용품"}, "1014": {"생활용품"},
    "1015": {"가구/홈인테리어"}, "1016": {"가전디지털"}, "1017": {"스포츠/레저용품"},
    "1018": {"자동차용품"}, "1020": {"완구/취미"}, "1021": {"문구/사무용품"},
    "1024": {"헬스/건강식품"}, "1029": {"반려/애완용품"},
}


def best(category_id, limit=20):
    """카테고리 베스트. 쿠팡이 매긴 판매 인기 순위(rank)가 함께 온다. 분야가 다른 상품은 뺀다."""
    items = call("GET", f"/products/bestcategories/{category_id}",
                 {"limit": limit, "subId": sub_id(), "imageSize": "512x512"}) or []
    match = BEST_MATCH.get(str(category_id))
    return [i for i in items if i.get("categoryName") in match] if match else items


def search(keyword, limit=10):
    data = call("GET", "/products/search", {"keyword": keyword, "limit": limit, "subId": sub_id(),
                                             "imageSize": "512x512"}) or {}
    return data.get("productData", []) if isinstance(data, dict) else data


def deeplink(urls):
    return call("POST", "/deeplink", body={"coupangUrls": list(urls), "subId": sub_id()}) or []


def report(kind, start, end):
    """kind: clicks | orders | cancels | commission. 날짜는 yyyyMMdd"""
    return call("GET", f"/reports/{kind}", {"startDate": start, "endDate": end}) or []


# ── 알림 / 요약 ──────────────────────────────────────────────

def notify(text):
    """카카오톡(나에게 보내기)·텔레그램 중 설정된 곳으로 보낸다. 없으면 조용히 넘어간다."""
    sent = False
    if os.environ.get("KAKAO_REST_KEY", "").strip() and os.environ.get("KAKAO_REFRESH_TOKEN", "").strip():
        try:
            kakao_send(text)
            sent = True
        except Exception as e:  # 알림 실패로 작업 전체를 실패시키지 않는다
            print("카카오톡 전송 실패:", e)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if token and chat:
        body = urllib.parse.urlencode({"chat_id": chat, "text": text, "disable_web_page_preview": "true"}).encode()
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=body, timeout=20)
            sent = True
        except Exception as e:
            print("텔레그램 전송 실패:", e)
    if not sent:
        print("(카카오톡·텔레그램 미설정 또는 실패 - 알림 생략)")


# ── 카카오톡 나에게 보내기 ─────────────────────────────────────
# Secrets: KAKAO_REST_KEY (앱 REST API 키), KAKAO_REFRESH_TOKEN (kakao-setup 작업이 저장),
#          KAKAO_CLIENT_SECRET (앱에서 Client Secret 을 켠 경우만)
# 카카오 토큰은 두 달이면 만료돼 새로 받은 토큰을 GH_PAT 로 Secrets 에 다시 저장한다.
KAKAO_REDIRECT = "https://kingdom.papalaqi.com"
KAKAO_SITE = "https://kingdom.papalaqi.com/"


def save_secret(name, value):
    """GH_PAT 로 저장소 Secret 을 바꾼다. 실패해도 작업은 계속한다."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not os.environ.get("GH_TOKEN", "").strip() or not repo:
        print(f"GH_PAT 가 없어 {name} 를 저장하지 못했습니다.")
        return False
    import subprocess
    r = subprocess.run(["gh", "secret", "set", name, "--repo", repo], input=value, text=True, capture_output=True)
    if r.returncode != 0:
        print(f"{name} 저장 실패:", r.stderr.strip()[:300])
        return False
    print(f"{name} 를 새 값으로 저장했습니다.")
    return True


def kakao_token(**data):
    """카카오 토큰 발급(authorization_code) / 갱신(refresh_token)."""
    data["client_id"] = os.environ.get("KAKAO_REST_KEY", "").strip()
    secret = os.environ.get("KAKAO_CLIENT_SECRET", "").strip()
    if secret:
        data["client_secret"] = secret
    req = urllib.request.Request("https://kauth.kakao.com/oauth/token", data=urllib.parse.urlencode(data).encode())
    req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            tok = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"카카오 토큰 오류 {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None
    for k in ("access_token", "refresh_token"):
        if tok.get(k):
            print(f"::add-mask::{tok[k]}")
    return tok


def kakao_send(text):
    tok = kakao_token(grant_type="refresh_token", refresh_token=os.environ["KAKAO_REFRESH_TOKEN"].strip())
    if tok.get("refresh_token"):   # 만료 한 달 전부터 새 refresh_token 이 온다
        save_secret("KAKAO_REFRESH_TOKEN", tok["refresh_token"])
    template = {"object_type": "text", "text": text[:200], "button_title": "KINGDOM 열기",
                "link": {"web_url": KAKAO_SITE, "mobile_web_url": KAKAO_SITE}}
    body = urllib.parse.urlencode({"template_object": json.dumps(template, ensure_ascii=False)}).encode()
    req = urllib.request.Request("https://kapi.kakao.com/v2/api/talk/memo/default/send", data=body)
    req.add_header("Authorization", f"Bearer {tok['access_token']}")
    try:
        urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"카카오 전송 오류 {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None


def summary(markdown):
    """Actions 실행 결과 화면에 표시"""
    print(markdown)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(markdown + "\n")


def now_kst():
    return datetime.now(KST)
