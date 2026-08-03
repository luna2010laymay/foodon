import React, { useState } from "react";
import { track } from "./analytics";

/* 상품 상세 맨 아래 — "만드는 사람에게 한마디" 제작자 피드백 보내기
   보낸 내용은 PostHog의 creator_feedback 이벤트로 쌓임(제작자가 PostHog에서 확인) */

const C = { ink: "#23291F", sub: "#6E7468", line: "#E5E2D9", sage: "#2F6D54", soft: "#EEF5F1" };

export default function CreatorFeedback({ product }) {
  const [msg, setMsg] = useState("");
  const [sent, setSent] = useState(false);

  const send = () => {
    const text = msg.trim();
    if (!text) return;
    track("creator_feedback", {
      message: text,
      product_id: product && product.id,
      product_name: product && product.name,
    });
    setSent(true);
    setMsg("");
  };

  return (
    <div style={{ marginTop: 22, background: C.soft, border: "1px solid " + C.line, borderRadius: 16, padding: "16px 16px 18px" }}>
      <div style={{ fontSize: 14, fontWeight: 800, color: C.ink }}>만드는 사람에게 한마디 ✍️</div>
      <div style={{ fontSize: 12.5, color: C.sub, lineHeight: 1.65, marginTop: 6 }}>
        푸드온이 진짜 앱으로 나온다면, 있었으면 하는 기능·아쉬운 점·응원 무엇이든 남겨주세요. 큰 힘이 돼요.
      </div>
      {sent ? (
        <div style={{ marginTop: 12, background: "#fff", border: "1px solid " + C.line, borderRadius: 12,
          padding: "15px", textAlign: "center", color: C.sage, fontSize: 13.5, fontWeight: 700 }}>
          소중한 의견 고마워요! 잘 담아둘게요 🌱
        </div>
      ) : (
        <>
          <textarea value={msg} onChange={(e) => setMsg(e.target.value)} rows={3}
            placeholder="여기에 자유롭게 적어주세요"
            style={{ width: "100%", boxSizing: "border-box", marginTop: 11, resize: "vertical",
              border: "1px solid " + C.line, borderRadius: 12, padding: "11px 12px", fontSize: 13.5,
              fontFamily: "inherit", color: C.ink, outline: "none", background: "#fff", lineHeight: 1.5 }} />
          <button onClick={send} disabled={!msg.trim()}
            style={{ width: "100%", marginTop: 10, background: msg.trim() ? C.sage : "#C4CDBF", color: "#fff",
              border: "none", borderRadius: 12, padding: "13px", fontSize: 14.5, fontWeight: 800,
              fontFamily: "inherit", cursor: msg.trim() ? "pointer" : "default" }}>
            보내기
          </button>
        </>
      )}
    </div>
  );
}
