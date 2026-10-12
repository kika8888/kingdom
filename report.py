"""매일 아침: 어제 클릭·주문·수익을 모아 텔레그램과 Actions 화면에 보낸다.

수익 정보는 공개 웹페이지(docs)에 절대 쓰지 않는다.
"""
import sys
from datetime import timedelta
from pathlib import Path

import partners as p

# GitHub 예약 실행은 붐비면 늦거나 빠진다. 그래서 매시간 수집 때도 `report.py --once` 를 돌려
# 아침 8시 이후 아직 안 보냈으면 그때 보낸다. 보낸 날짜를 여기 남겨 하루 한 번만 간다.
# (docs 폴더는 매시간 수집이 저장하므로 여기에 날짜만 남긴다. 수익 숫자는 절대 쓰지 않는다)
SENT = Path(__file__).parent / "docs" / "report_sent.txt"


def total(rows, *fields):
    s = 0
    for r in rows or []:
        for f in fields:
            v = r.get(f)
            if isinstance(v, (int, float)):
                s += v
                break
            if isinstance(v, str) and v.replace(".", "", 1).lstrip("-").isdigit():
                s += float(v)
                break
    return s


def main(once=False):
    now = p.now_kst()
    today = now.strftime("%Y-%m-%d")
    import os
    if not once and os.environ.get("GITHUB_EVENT_NAME") == "schedule":
        # 09:10 예약 실행은 기록을 저장하지 못해 중복될 수 있으므로, 실제 전송은 매시간 수집이 맡는다
        print("실적 알림은 매시간 수집(08시 이후 첫 실행)에서 보냅니다.")
        return
    if once or "--once" in sys.argv:
        if now.hour < 8:
            print("아침 8시 전이라 실적 알림은 나중에 보냅니다.")
            return
        if SENT.exists() and SENT.read_text(encoding="utf-8").strip() == today:
            print("오늘 실적 알림은 이미 보냈습니다.")
            return

    day = now - timedelta(days=1)
    d = day.strftime("%Y%m%d")

    clicks = total(p.report("clicks", d, d), "click", "clickCount")
    orders_rows = p.report("orders", d, d)
    orders = total(orders_rows, "orderCount", "quantity")
    gmv = total(orders_rows, "gmv", "orderAmount")
    commission = total(p.report("commission", d, d), "commission")

    label = day.strftime("%Y-%m-%d")
    errors = p.notify(
        f"[쿠팡 파트너스] {label} 실적\n"
        f"클릭 {clicks:,.0f}회\n"
        f"주문 {orders:,.0f}건 (구매액 {gmv:,.0f}원)\n"
        f"수익 {commission:,.0f}원"
    )
    p.summary(
        f"## {label} 실적\n\n| 클릭 | 주문 | 구매액 | 수익 |\n|---:|---:|---:|---:|\n"
        f"| {clicks:,.0f} | {orders:,.0f} | {gmv:,.0f}원 | {commission:,.0f}원 |\n\n"
        "※ 쿠팡 리포트는 하루 정도 늦게 확정될 수 있습니다."
    )
    if errors:   # 알림이 안 갔으면 실패로 표시해서 GitHub 실행 기록(빨간 X)과 메일로 알 수 있게
        for e in errors:
            print(f"::error title=알림 전송 실패::{e[:300]}")
        raise SystemExit("실적 알림을 보내지 못했습니다: " + " / ".join(errors))
    SENT.parent.mkdir(exist_ok=True)
    SENT.write_text(today, encoding="utf-8")


if __name__ == "__main__":
    main()
