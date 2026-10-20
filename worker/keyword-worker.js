// KINGDOM 키워드 전략팀 중계 서버 (Cloudflare Workers, 무료)
// 네이버 검색광고 API(검색수·클릭수·경쟁도) + 네이버 검색 API(블로그 문서 수)를 대신 불러 준다.
// 키는 Cloudflare 설정 > 변수(Secrets)에만 넣는다. 이 코드에는 키가 없다.
//   SEARCHAD_API_KEY, SEARCHAD_SECRET, SEARCHAD_CUSTOMER_ID, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
// 사용: GET https://<워커주소>/?kw=캠핑의자            → 연관 키워드 표(최대 100개, 문서 수는 위 30개)
//       GET https://<워커주소>/?kw=캠핑의자&docs=all   → 문서 수를 전부(최대 100개) 조회

const ALLOW = ["https://kingdom.papalaqi.com", "https://kika8888.github.io"];

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": ALLOW.includes(origin) ? origin : ALLOW[0],
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Content-Type": "application/json; charset=utf-8",
    };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    const url = new URL(req.url);
    const kw = (url.searchParams.get("kw") || "").trim();
    if (!kw) return json({ error: "키워드를 넣어 주세요 (?kw=)" }, 400, cors);
    if (kw.length > 40) return json({ error: "키워드가 너무 길어요" }, 400, cors);
    try {
      const rows = await searchad(env, kw.replace(/\s+/g, ""));
      const limit = url.searchParams.get("docs") === "all" ? 100 : 30;
      await Promise.all(rows.slice(0, limit).map(async (r) => { r.docs = await blogTotal(env, r.keyword); }));
      return json({ keyword: kw, count: rows.length, rows }, 200, cors);
    } catch (e) {
      return json({ error: String(e.message || e) }, 502, cors);
    }
  },
};

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers });
}

const clean = (v) => String(v ?? "").replace(/[\s\u200b\ufeff]/g, "");   // 복사할 때 딸려 온 띄어쓰기·줄바꿈 제거
const num = (v) => (typeof v === "number" ? v : String(v).includes("<") ? 5 : Number(String(v).replace(/[^\d.]/g, "")) || 0);

async function searchad(env, hint) {
  const path = "/keywordstool";
  const ts = String(Date.now());
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(clean(env.SEARCHAD_SECRET)),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${ts}.GET.${path}`));
  const signature = btoa(String.fromCharCode(...new Uint8Array(sig)));
  const res = await fetch(`https://api.searchad.naver.com${path}?hintKeywords=${encodeURIComponent(hint)}&showDetail=1`, {
    headers: { "X-Timestamp": ts, "X-API-KEY": clean(env.SEARCHAD_API_KEY), "X-Customer": clean(env.SEARCHAD_CUSTOMER_ID).replace(/\D/g, ""), "X-Signature": signature },
  });
  if (!res.ok) {
    const msg = (await res.text()).replace(/0100000000[0-9a-f]+/gi, "(키 숨김)").slice(0, 400);
    throw new Error(`검색광고 API 오류 ${res.status}: ${msg} | 넣은 CUSTOMER_ID 숫자 길이 ${clean(env.SEARCHAD_CUSTOMER_ID).replace(/\D/g, "").length}자`);
  }
  const data = await res.json();
  return (data.keywordList || []).slice(0, 100).map((k) => {
    const pc = num(k.monthlyPcQcCnt), mo = num(k.monthlyMobileQcCnt);
    return {
      keyword: k.relKeyword, pc, mo, total: pc + mo,
      pcClick: num(k.monthlyAvePcClkCnt), moClick: num(k.monthlyAveMobileClkCnt),
      adComp: k.compIdx || "", adDepth: num(k.plAvgDepth), docs: null,
    };
  });
}

async function blogTotal(env, q) {
  if (!env.NAVER_CLIENT_ID || !env.NAVER_CLIENT_SECRET) return null;   // 개발자센터 검색 API 키가 없으면 문서 수는 비워 둔다
  try {
    const res = await fetch(`https://openapi.naver.com/v1/search/blog.json?query=${encodeURIComponent(q)}&display=1`, {
      headers: { "X-Naver-Client-Id": env.NAVER_CLIENT_ID, "X-Naver-Client-Secret": env.NAVER_CLIENT_SECRET },
    });
    if (!res.ok) return null;
    return (await res.json()).total ?? null;
  } catch { return null; }
}
