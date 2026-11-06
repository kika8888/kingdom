// KINGDOM 깨우기 (Cloudflare Workers 무료, Cron Triggers)
// GitHub 예약 실행은 붐비면 늦거나 빠진다. 매시간 확인해서, 빠진 작업만 대신 실행을 건다.
//   매시 22분: 이번 시간 07분 상품 수집(collect)이 돌았나? 안 돌았으면 실행
//   매시 02분: 지난 47분 블로그→스레드(blog)가 돌았나? 안 돌았으면 실행
// GitHub 가 제때 돌았으면 아무것도 하지 않으므로 두 번 돌지 않는다.
// 비밀값: GH_TOKEN (kika8888/kingdom 의 Actions 읽기·쓰기 권한 토큰) — Cloudflare 설정 > 변수(Secret)에만 넣는다.
// Cron Triggers: "22 * * * *", "2 * * * *"

const REPO = "https://api.github.com/repos/kika8888/kingdom";
const CHECK = { "22 * * * *": "collect", "2 * * * *": "blog" };
const WINDOW_MIN = 25;   // 이 시간 안에 그 작업이 실행됐으면 돌았다고 본다

export default {
  async scheduled(event, env, ctx) {
    const task = CHECK[event.cron];
    if (task) ctx.waitUntil(wake(env, task));
  },
  // 주소로 들어오면 상태만 보여 준다 (아무나 실행을 걸 수 없게)
  async fetch() {
    return new Response("KINGDOM wake worker: 매시 22분 collect, 02분 blog 확인", { headers: { "Content-Type": "text/plain; charset=utf-8" } });
  },
};

async function gh(env, path, init = {}) {
  return fetch(REPO + path, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json",
      "User-Agent": "kingdom-wake", "Content-Type": "application/json",
    },
  });
}

async function ranRecently(env, task) {
  const since = Date.now() - WINDOW_MIN * 60 * 1000;
  const res = await gh(env, "/actions/runs?per_page=10");
  if (!res.ok) throw new Error(`실행 목록 오류 ${res.status}`);
  const runs = (await res.json()).workflow_runs.filter((r) => Date.parse(r.created_at) >= since);
  for (const r of runs) {
    const jr = await gh(env, `/actions/runs/${r.id}/jobs`);
    if (!jr.ok) continue;
    const jobs = (await jr.json()).jobs || [];
    // 대기·실행 중이거나 끝났는데 건너뜀(skipped)이 아니면 그 작업이 돈 것
    if (jobs.some((j) => j.name === task && j.conclusion !== "skipped")) return true;
  }
  return false;
}

async function wake(env, task) {
  try {
    if (await ranRecently(env, task)) {
      console.log(`${task}: GitHub 가 제때 실행함 → 그대로 둠`);
      return;
    }
    const res = await gh(env, "/actions/workflows/kingdom.yml/dispatches", {
      method: "POST", body: JSON.stringify({ ref: "main", inputs: { task } }),
    });
    console.log(`${task}: 빠져서 대신 실행 → ${res.status}`);
  } catch (e) {
    console.log(`${task}: 확인 실패 ${e.message}`);
  }
}
