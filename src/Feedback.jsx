import React, { useState } from "react";
import { track } from "./analytics";

/* 제품 상세 맨 아래 — "만드는 사람에게 한마디" 제작자 피드백 보내기
   PostHog creator_feedback 이벤트로 수집 (would_use / good / wish)
   ⚠️ Choice·Field 는 반드시 컴포넌트 바깥에 정의할 것.
      안에서 정의하면 매 렌더마다 새 컴포넌트가 되어 textarea 가 리마운트→포커스가 날아감(한 글자만 입력됨). */

const C = { ink: "#23291F", sub: "#6E7468", line: "#E5E2D9", sage: "#2F6D54", soft: "#EEF5F1" };

const OPTS = [
  { key: "need", label: "완전 필요한 앱이에요, 나오면 쓸래요! 🥰", tone: "#2F6D54" },
  { key: "improve", label: "쓸 것 같아요, 조금만 보완되면 좋겠어요 🙂", tone: "#8A6D2F" },
  { key: "maybe_not", label: "꼭 필요하진 않은 것 같아요 🌱", tone: "#8A9086" },
];

function Choice({ o, active, onClick }) {
  return (
    <button onClick={onClick}
      style={{ width: "100%", textAlign: "left", padding: "12px 14px", borderRadius: 12, cursor: "pointer",
        fontFamily: "inherit", fontSize: 13.5, fontWeight: 700, border: "1.5px solid " + (active ? o.tone : C.line),
        background: active ? o.tone : "#fff", color: active ? "#fff" : C.ink }}>
      {o.label}
    </button>
  );
}

function Field({ chipBg, chipTx, chip, value, onChange, placeholder }) {
  return (
    <div style={{ marginTop: 12 }}>
      <span style={{ display: "inline-block", fontSize: 12, fontWeight: 700, color: chipTx, background: chipBg,
        borderRadius: 8, padding: "4px 10px", marginBottom: 7 }}>{chip}</span>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={2} placeholder={placeholder}
        style={{ width: "100%", boxSizing: "border-box", resize: "vertical",
          border: "1px solid " + C.line, borderRadius: 12, padding: "11px 12px", fontSize: 13.5,
          fontFamily: "inherit", color: C.ink, outline: "none", background: "#fff", lineHeight: 1.5 }} />
    </div>
  );
}

export default function CreatorFeedback({ product }) {
  const [good, setGood] = useState("");
  const [wish, setWish] = useState("");
  const [use, setUse] = useState(null); // null | "need" | "improve" | "maybe_not"
  const [sent, setSent] = useState(false);

  const canSend = good.trim() || wish.trim() || use !== null;

  const send = () => {
    if (!canSend) return;
    track("creator_feedback", {
      good: good.trim(),
      wish: wish.trim(),
      would_use: use,
      product_id: product && product.id,
      product_name: product && product.name,
    });
    setSent(true);
    setGood("");
    setWish("");
  };

  return (
    <div style={{ marginTop: 22, background: C.soft, border: "1px solid " + C.line, borderRadius: 16, padding: "16px 16px 18px" }}>
      <div style={{ fontSize: 14, fontWeight: 800, color: C.ink }}>만드는 사람에게 한마디 ✍️</div>
      <div style={{ fontSize: 12.5, color: C.sub, lineHeight: 1.65, marginTop: 6 }}>
        푸드온이 진짜 앱으로 나온다면, 좋았던 점·아쉬운 점·바라는 기능 무엇이든 남겨주세요. 큰 힘이 돼요.
      </div>
      {sent ? (
        <div style={{ marginTop: 12, background: "#fff", border: "1px solid " + C.line, borderRadius: 12,
          padding: "15px", textAlign: "center", color: C.sage, fontSize: 13.5, fontWeight: 700 }}>
          소중한 의견 고마워요! 잘 담아둘게요 🌱
        </div>
      ) : (
        <>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: C.ink, marginTop: 14, marginBottom: 8 }}>
            혹시, 실제 앱으로 나오면 어떨 것 같으세요?
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
            {OPTS.map((o) => (
              <Choice key={o.key} o={o} active={use === o.key}
                onClick={() => setUse(use === o.key ? null : o.key)} />
            ))}
          </div>
          <Field chipBg="#E7F1EA" chipTx="#2C7A54" chip="☺ 좋았던 점"
            value={good} onChange={setGood} placeholder="마음에 든 점, 편했던 기능 등 (선택)" />
          <Field chipBg="#FBE6D2" chipTx="#C0692A" chip="✨ 아쉬운 점 · 바라는 점"
            value={wish} onChange={setWish} placeholder="아쉬웠던 점, 있었으면 하는 기능 등 (선택)" />
          <button onClick={send} disabled={!canSend}
            style={{ width: "100%", marginTop: 12, background: canSend ? C.sage : "#C4CDBF", color: "#fff",
              border: "none", borderRadius: 12, padding: "13px", fontSize: 14.5, fontWeight: 800,
              fontFamily: "inherit", cursor: canSend ? "pointer" : "default" }}>
            보내기
          </button>
        </>
      )}
    </div>
  );
}
