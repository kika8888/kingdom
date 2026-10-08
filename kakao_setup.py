"""처음 한 번: 카카오 로그인 뒤 주소창에 나온 code 를 넣으면 카톡 알림을 연결한다.

GitHub > Actions > KINGDOM > Run workflow > task 를 kakao-setup, code 칸에 값을 넣고 실행.
받은 토큰은 Secrets 의 KAKAO_REFRESH_TOKEN 에 저장되고, 내 카톡으로 시험 메시지가 간다.
code 는 10분 안에 한 번만 쓸 수 있다.
"""
import os

import partners as p


def main():
    if not os.environ.get("KAKAO_REST_KEY", "").strip():
        raise SystemExit("KAKAO_REST_KEY 가 없습니다. 저장소 Secrets 에 카카오 REST API 키를 먼저 넣어 주세요.")
    raw = os.environ.get("KAKAO_CODE", "").strip()
    code = raw.split("code=", 1)[1].split("&")[0] if "code=" in raw else raw   # 주소 전체를 붙여 넣어도 된다
    if not code:
        raise SystemExit("code 칸이 비어 있습니다. 카카오 로그인 뒤 주소창의 code= 뒤 값을 넣어 주세요.")
    print(f"::add-mask::{code}")

    tok = p.kakao_token(grant_type="authorization_code", redirect_uri=p.KAKAO_REDIRECT, code=code)
    if not tok.get("refresh_token"):
        raise SystemExit("카카오가 토큰을 주지 않았습니다. 처음부터 다시 로그인해 주세요.")
    if not p.save_secret("KAKAO_REFRESH_TOKEN", tok["refresh_token"]):
        raise SystemExit("토큰을 Secrets 에 저장하지 못했습니다. GH_PAT 를 확인해 주세요.")

    os.environ["KAKAO_REFRESH_TOKEN"] = tok["refresh_token"]
    p.kakao_send("[KINGDOM] 카카오톡 알림이 연결됐어요 🎉\n매일 아침 9시쯤 어제 실적을 보내드릴게요.")
    p.summary("## 카카오톡 연결 완료\n\n내 카톡 '나와의 채팅'에 시험 메시지를 보냈습니다.")


if __name__ == "__main__":
    main()
