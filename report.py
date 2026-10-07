"""매일 아침: 어제 클릭·주문·수익을 모아 텔레그램과 Actions 화면에 보낸다.

수익 정보는 공개 웹페이지(docs)에 절대 쓰지 않는다.
"""
from datetime import timedelta

import partners as p


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


def main():
    day = p.now_kst() - timedelta(days=1)
    d = day.strftime("%Y%m%d")

    clicks = total(p.report("clicks", d, d), "click", "clickCount")
    orders_rows = p.report("orders", d, d)
    orders = total(orders_rows, "orderCount", "quantity")
    gmv = total(orders_rows, "gmv", "orderAmount")
    commission = total(p.report("commission", d, d), "commission")

    label = day.strftime("%Y-%m-%d")
    p.notify(
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


if __name__ == "__main__":
    main()
