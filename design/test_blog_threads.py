"""게시 없이: 최근 블로그 글로 스레드 글을 만들어 보여 준다."""
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # 저장소 맨 위 (blog_threads.py 가 있는 곳)
import blog_threads as b

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
for acc in b.ACCOUNTS:
    u = (f"https://blog.naver.com/PostTitleListAsync.naver?blogId={acc['blog']}&currentPage=1"
         f"&categoryNo=0&parentCategoryNo=0&countPerPage={N}")
    t = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})).read().decode()
    for no in re.findall(r'"logNo":"(\d+)"', t)[:N]:
        link = f"https://blog.naver.com/{acc['blog']}/{no}"
        x = b.post_meta(link)
        text = b.compose(x, acc, {}, b.post_text(link))
        print(f"===== {acc['name']} {len(text)}자 =====\n{text}\n")

if len(sys.argv) > 2:
    link = sys.argv[2]
    acc = b.ACCOUNTS[0] if "soduwk1209" in link else b.ACCOUNTS[1]
    print(b.compose(b.post_meta(link), acc, {}, b.post_text(link)))
