"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import styles from "@/app/admin-shell.module.css";
import AppShell from "@/app/components/app-shell";
import { createSchedule, fetchMetaOptions, fetchSchedules, type ScheduleRow } from "@/lib/api";

const WEEK_NAMES = ["일", "월", "화", "수", "목", "금", "토"];

export default function SchedulePage() {
  const [rows, setRows] = useState<ScheduleRow[]>([]);
  const [opts, setOpts] = useState<{ job_types: string[]; job_statuses: string[] }>({ job_types: [], job_statuses: [] });
  const [message, setMessage] = useState("");
  const [calendarDate, setCalendarDate] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1);
  });

  async function load() {
    const [schedules, options] = await Promise.all([fetchSchedules({ page: 1, size: 15 }), fetchMetaOptions()]);
    setRows(schedules.data);
    setOpts({ job_types: options.data.job_types, job_statuses: options.data.job_statuses });
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void load();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const todayStr = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const calendarCells = useMemo(() => {
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const cells: Array<{ day: number | null; dateText: string | null; isToday: boolean }> = [];

    for (let i = 0; i < firstDay; i += 1) {
      cells.push({ day: null, dateText: null, isToday: false });
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const dateText = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      cells.push({ day, dateText, isToday: dateText === todayStr });
    }

    while (cells.length % 7 !== 0) {
      cells.push({ day: null, dateText: null, isToday: false });
    }

    return cells;
  }, [calendarDate, todayStr]);

  return (
    <AppShell styles={styles} activeHref="/schedule" searchPlaceholder="Search schedules">
        <main className={styles.page}>
          <section className={styles.sectionCard}>
            <header className={styles.header}><h1>스케줄</h1><Link href="/">← 대시보드</Link></header>

            <div className={styles.calendarPanel}>
              <div className={styles.calendarHeader}>
                <button type="button" onClick={() => setCalendarDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))}>◀</button>
                <strong>
                  {calendarDate.getFullYear()}년 {calendarDate.getMonth() + 1}월
                </strong>
                <button type="button" onClick={() => setCalendarDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))}>▶</button>
              </div>

              <div className={styles.calendarWeekRow}>
                {WEEK_NAMES.map((name) => (
                  <div key={name}>{name}</div>
                ))}
              </div>

              <div className={styles.calendarGrid}>
                {calendarCells.map((cell, idx) => (
                  <div key={`${cell.dateText ?? "empty"}-${idx}`} className={cell.isToday ? styles.calendarCellToday : styles.calendarCell}>
                    {cell.day ?? ""}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className={styles.sectionCard}>
            <h2>스케줄 등록</h2>
            <form
              className={styles.panel}
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                await createSchedule({
                  job_name: String(fd.get("job_name") || ""),
                  job_type: String(fd.get("job_type") || "REPORT"),
                  status: String(fd.get("status") || "PENDING"),
                  next_run_at: String(fd.get("next_run_at") || ""),
                  payload_note: String(fd.get("payload_note") || ""),
                });
                setMessage("스케줄 저장 완료");
                await load();
              }}
            >
              <div className={styles.formGrid}>
                <label className={styles.field}>작업명<input name="job_name" required /></label>
                <label className={styles.field}>작업타입<select name="job_type">{opts.job_types.map((t) => <option key={t}>{t}</option>)}</select></label>
                <label className={styles.field}>상태<select name="status">{opts.job_statuses.map((s) => <option key={s}>{s}</option>)}</select></label>
                <label className={styles.field}>실행일시<input name="next_run_at" type="datetime-local" required /></label>
              </div>
              <label className={styles.field}>메모<textarea name="payload_note" rows={2} /></label>
              <div className={styles.actions}><button className={styles.primaryBtn}>Save</button></div>
            </form>
            {message ? <p>{message}</p> : null}
          </section>

          <section className={styles.sectionCard}>
            <h2>등록 스케줄</h2>
            <div className={styles.panel}>
              <table className={styles.table}>
                <thead><tr><th>ID</th><th>작업명</th><th>타입</th><th>상태</th><th>다음 실행</th></tr></thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id}><td>{r.id}</td><td>{r.job_name}</td><td>{r.job_type}</td><td>{r.status}</td><td>{r.next_run_at ?? "-"}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </main>
    </AppShell>
  );
}
