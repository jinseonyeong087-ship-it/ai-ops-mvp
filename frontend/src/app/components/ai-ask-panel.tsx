"use client";

import { useState, type FormEvent } from "react";
import { askOps } from "@/lib/api";
import styles from "./ai-ask-panel.module.css";

export default function AiAskPanel() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [source, setSource] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = question.trim();
    if (!trimmed) {
      setError("질문을 입력해 주세요.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await askOps(trimmed);
      setAnswer(result.answer);
      setSource(result.source);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "AI 질의 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className={styles.panel} aria-label="AI 질의 패널">
      <h2>AI 질의 패널</h2>
      <p className={styles.description}>운영 질문을 입력하면 AI 요약/분석 응답을 제공합니다.</p>

      <form className={styles.form} onSubmit={onSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="예) 지난 7일 재고 위험 요약해줘"
          rows={3}
          maxLength={500}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "질의 중..." : "AI에게 질문"}
        </button>
      </form>

      {error ? <p className={styles.error}>{error}</p> : null}

      {answer ? (
        <div className={styles.answerBox}>
          <p className={styles.answerTitle}>응답</p>
          <p>{answer}</p>
          <small>source: {source || "unknown"}</small>
        </div>
      ) : null}
    </section>
  );
}
