"""원할 때: 쿠팡 상품 주소를 넣으면 내 파트너스 링크로 바꿔 준다.

GitHub > Actions > "링크 만들기" > Run workflow 에 주소를 넣어 실행.
여러 개는 쉼표나 줄바꿈으로 구분 (한 번에 최대 20개)
"""
import os
import re

import partners as p


def main():
    raw = os.environ.get("INPUT_URLS", "")
    urls = [u for u in re.split(r"[\s,]+", raw) if u.startswith("http")]
    if not urls:
        raise SystemExit("쿠팡 상품 주소를 입력해 주세요. (https://www.coupang.com/vp/products/...)")

    rows = p.deeplink(urls[:20])
    lines = ["## 만든 링크", "", "| 원래 주소 | 파트너스 링크 |", "|---|---|"]
    msg = ["[쿠팡 파트너스] 링크"]
    for r in rows:
        short = r.get("shortenUrl") or r.get("landingUrl")
        lines.append(f"| {r.get('originalUrl', '')} | {short} |")
        msg.append(short)
    p.summary("\n".join(lines))
    p.notify("\n".join(msg))


if __name__ == "__main__":
    main()
