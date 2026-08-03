import React, { useState } from "react";

/* =====================================================================
   푸드온 온보딩 — 앱을 열 때마다 매번 노출 (3페이지)
   - "시작하기" 또는 "건너뛰기"를 누르면 그 세션에서만 닫힘
   - 새로고침·재접속하면 다시 나타남 (저장 안 함)
   ===================================================================== */

const C = {
  ink: "#22201C",
  sub: "#6E7468",
  sage: "#2F6D54",
  line: "rgba(34,32,28,.16)",
  // 앱 성분 태그 색과 맞춤
  allergyBg: "#FBE6D2", allergyTx: "#C0692A",
  addBg: "#E7EDF1", addTx: "#4A6373",
  animalBg: "#E9E5F0", animalTx: "#5E5478",
  compBg: "#EAE4D7", compTx: "#7A6A50",
};

function Check({ size = 15, stroke = "#fff", sw = 4 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M5 12.4l4.4 4.4L19 7" stroke={stroke} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const PAGES = [
  {
    title: ["성분으로 검색해서", "직접 골라요"],
    desc: ["내가 먹고 싶은 식품을", "전성분으로 찾아보고 직접 확인해요."],
    hero: (
      <>
        <div style={{ display: "flex", alignItems: "center", gap: 10, background: "#fff", borderRadius: 16,
          padding: "16px 18px", boxShadow: "0 14px 30px -14px rgba(36,80,63,.4)" }}>
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke={C.sage} strokeWidth="2.2" />
            <path d="M20 20l-4-4" stroke={C.sage} strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span style={{ fontSize: 16, color: "#8a857b" }}>그래놀라</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 9, marginTop: 20 }}>
          <Chip>귀리</Chip>
          <Chip bg={C.allergyBg} bd="#f0d3b6" fg={C.allergyTx}>대두 · 알러지</Chip>
          <Chip bg={C.animalBg} bd="#dcd4e8" fg={C.animalTx}>꿀 · 동물성</Chip>
          <Chip>아몬드</Chip>
        </div>
        <ResultCard emoji="🥣" sub="오트빌 · 시리얼" name="오리지널 그래놀라" />
      </>
    ),
  },
  {
    title: ["나에게 맞는 먹거리를", "더 쉽게 찾아요"],
    desc: ["알러지·채식·첨가물 조건으로", "내게 맞는 식품만 골라서 확인해요."],
    hero: (
      <>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 9 }}>
          <Toggle on>동물성 빼기</Toggle>
          <Toggle on>알러지 빼기</Toggle>
          <Toggle>첨가물 빼기</Toggle>
        </div>
        <div style={{ background: "#fff", borderRadius: 18, padding: 16, marginTop: 20,
          boxShadow: "0 12px 28px -16px rgba(36,80,63,.36)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 13 }}>
            <div style={{ width: 52, height: 52, borderRadius: 12, background: "#eef3ec",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, flexShrink: 0 }}>🥛</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, color: "#8a857b" }}>콩담은 · 음료</div>
              <div style={{ fontSize: 15.5, fontWeight: 700 }}>클래식 두유</div>
            </div>
            <span style={{ width: 28, height: 28, borderRadius: "50%", background: C.sage,
              display: "inline-flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}><Check size={18} /></span>
          </div>
          <div style={{ height: 1, background: "rgba(34,32,28,.07)", margin: "14px 0" }} />
          <div style={{ display: "flex", gap: 7 }}>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: C.allergyTx, background: C.allergyBg, borderRadius: 7, padding: "5px 10px" }}>알러지 · 대두</span>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: C.sub, background: "#f1efe9", borderRadius: 7, padding: "5px 10px" }}>동물성 없음</span>
          </div>
        </div>
      </>
    ),
  },
  {
    title: ["어려운 성분도", "쉽게 풀어드려요"],
    desc: ["성분을 톡 누르면 다정한 설명이 나오고,", "식약처 알레르기 유발물질은 눈에 띄게 알려줘요."],
    hero: (
      <>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 9 }}>
          <Chip>정제소금</Chip>
          <Chip bg={C.allergyBg} bd="#f0d3b6" fg={C.allergyTx}>밀가루</Chip>
          <Chip bg={C.addBg} bd="#cfdbe3" fg={C.addTx}>잔탄검</Chip>
        </div>

        {/* 성분 설명 카드 (알레르기 강조 예시) */}
        <div style={{ background: "#fff", borderRadius: 18, padding: 16, marginTop: 18,
          boxShadow: "0 12px 28px -16px rgba(36,80,63,.36)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 16, fontWeight: 800, color: C.ink }}>밀가루</span>
            <span style={{ fontSize: 11.5, fontWeight: 700, color: C.allergyTx, background: C.allergyBg,
              borderRadius: 7, padding: "3px 8px" }}>알레르기</span>
          </div>
          <div style={{ marginTop: 11, background: "#FCF0E6", border: "1px solid #F3D8BF",
            borderRadius: 12, padding: "11px 13px" }}>
            <div style={{ fontSize: 12.5, fontWeight: 800, color: C.allergyTx, marginBottom: 5 }}>
              ⚠️ 식약처 알레르기 유발물질
            </div>
            <div style={{ fontSize: 13.5, color: "#4a463f", lineHeight: 1.6 }}>
              밀을 곱게 빻은 하얀 가루예요. 글루텐 덕분에 반죽이 쫄깃하게 뭉쳐져서 빵·면·과자의 기본이 돼요. 밀 알레르기가 있으면 조심하세요.
            </div>
          </div>
        </div>

        {/* 성분 분석 미니 */}
        <div style={{ display: "flex", gap: 7, marginTop: 12 }}>
          <Stat n="7" label="알레르기" bg={C.allergyBg} fg={C.allergyTx} />
          <Stat n="5" label="첨가물" bg={C.addBg} fg={C.addTx} />
          <Stat n="3" label="복합" bg={C.compBg} fg={C.compTx} />
          <Stat n="2" label="동물성" bg={C.animalBg} fg={C.animalTx} />
        </div>
      </>
    ),
  },
];

function Chip({ children, bg = "#fff", bd = "#e7e3da", fg = "#3a3833" }) {
  return (
    <span style={{ fontSize: 14.5, fontWeight: 600, color: fg, background: bg,
      border: "1px solid " + bd, borderRadius: 10, padding: "9px 13px" }}>{children}</span>
  );
}
function Toggle({ children, on }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 14.5, fontWeight: on ? 700 : 600,
      color: on ? "#fff" : "#4a463f", background: on ? "#2F6D54" : "#fff",
      border: "1px solid " + (on ? "#2F6D54" : "rgba(34,32,28,.16)"), borderRadius: 12, padding: "10px 14px" }}>
      {on && <Check />}{children}
    </span>
  );
}
function Stat({ n, label, bg, fg }) {
  return (
    <div style={{ flex: 1, background: bg, borderRadius: 12, padding: "10px 6px", textAlign: "center" }}>
      <div style={{ fontSize: 18, fontWeight: 800, color: fg, lineHeight: 1 }}>{n}</div>
      <div style={{ fontSize: 11, fontWeight: 600, color: fg, marginTop: 4, opacity: .85 }}>{label}</div>
    </div>
  );
}
function ResultCard({ emoji, sub, name }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 13, background: "#fff", borderRadius: 18,
      padding: 14, marginTop: 20, boxShadow: "0 10px 26px -16px rgba(36,80,63,.34)" }}>
      <div style={{ width: 52, height: 52, borderRadius: 12, background: "#eef3ec",
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 27, flexShrink: 0 }}>{emoji}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, color: "#8a857b" }}>{sub}</div>
        <div style={{ fontSize: 15.5, fontWeight: 700 }}>{name}</div>
      </div>
      <span style={{ width: 28, height: 28, borderRadius: "50%", background: "#2F6D54",
        display: "inline-flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}><Check size={18} /></span>
    </div>
  );
}

export default function Onboarding() {
  const [done, setDone] = useState(false);
  const [page, setPage] = useState(0);

  if (done) return null;

  const finish = () => setDone(true);
  const next = () => (page < PAGES.length - 1 ? setPage(page + 1) : finish());
  const p = PAGES[page];

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 9999, overflow: "auto", background: "#FFFFFF",
      display: "flex", justifyContent: "center", padding: "24px 12px", fontFamily: "'Pretendard', -apple-system, sans-serif" }}>
      <div style={{ width: 390, maxWidth: "100%", minHeight: 760, background: "#fff", borderRadius: 28,
        overflow: "hidden", border: "1px solid #E5E2D9", boxShadow: "0 18px 50px rgba(35,41,31,.18)",
        display: "flex", flexDirection: "column", padding: "30px 0 0" }}>
        {/* skip */}
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "0 26px" }}>
          <button onClick={finish} style={{ border: "none", background: "transparent", fontSize: 15,
            color: "#a19c92", fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>건너뛰기</button>
        </div>

        {/* hero */}
        <div style={{ margin: "18px 24px 0", borderRadius: 32,
          background: "linear-gradient(162deg,#eef5f1 0%,#e0ede7 100%)", padding: "34px 26px 36px", flex: "none" }}>
          {p.hero}
        </div>

        {/* text */}
        <div style={{ padding: "38px 34px 0", flex: 1 }}>
          <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: "-.03em", lineHeight: 1.32, color: C.ink }}>
            {p.title[0]}<br />{p.title[1]}
          </div>
          <div style={{ fontSize: 16.5, color: C.sub, lineHeight: 1.62, marginTop: 16 }}>
            {p.desc[0]}<br />{p.desc[1]}
          </div>
        </div>

        {/* footer */}
        <div style={{ padding: "0 34px max(40px, env(safe-area-inset-bottom))" }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
            {PAGES.map((_, i) => (
              <span key={i} style={{ width: i === page ? 24 : 8, height: 8, borderRadius: 4,
                background: i === page ? C.sage : "#d6d2c8", transition: "width .2s ease" }} />
            ))}
          </div>
          <button onClick={next} style={{ width: "100%", background: C.sage, color: "#fff", border: "none",
            borderRadius: 18, padding: 19, fontSize: 17, fontWeight: 700, fontFamily: "inherit", cursor: "pointer" }}>
            {page < PAGES.length - 1 ? "다음" : "시작하기"}
          </button>
        </div>
      </div>
    </div>
  );
}
