import posthog from "posthog-js";

/* =====================================================================
   PostHog 연결 — 방문·검색·검색실패·상품/구매링크 클릭·제작자 피드백 수집
   - 키는 소스에 넣지 않고 환경변수로만 주입 (Vercel > Settings > Environment Variables)
       VITE_POSTHOG_KEY   = phc_...            (PostHog 프로젝트 API 키)
       VITE_POSTHOG_HOST  = https://us.i.posthog.com  (미국) 또는 https://eu.i.posthog.com (유럽)
   - 키가 없으면 모든 함수가 조용히 무시됨(로컬/미설정 배포에서 에러 없음)
   ===================================================================== */

const KEY = import.meta.env.VITE_POSTHOG_KEY;
const HOST = import.meta.env.VITE_POSTHOG_HOST || "https://us.i.posthog.com";
let ready = false;

export function initAnalytics() {
  if (ready || !KEY || typeof window === "undefined") return;
  try {
    posthog.init(KEY, {
      api_host: HOST,
      capture_pageview: true,   // 방문(페이지뷰) 자동 수집
      autocapture: true,        // 일반 클릭 자동 수집
      persistence: "localStorage+cookie",
    });
    ready = true;
  } catch (e) { /* noop */ }
}

export function track(event, props) {
  if (!KEY || !ready) return;
  try { posthog.capture(event, props); } catch (e) { /* noop */ }
}
