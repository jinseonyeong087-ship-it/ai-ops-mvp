"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import styles from "@/app/admin-shell.module.css";
import { fetchMetaOptions, fetchSalesDaily, upsertSalesDaily, type SalesDailyRow } from "@/lib/api";

const SIDE_MENUS = [
  { label: "Dashboard", href: "/" },
  { label: "상품 등록", href: "/products/new" },
  { label: "주문/배송", href: "/purchase-orders" },
  { label: "스케줄", href: "/schedule" },
  { label: "판매 현황", href: "/sales" },
];

export default function SalesPage() {
  const [rows, setRows] = useState<SalesDailyRow[]>([]);
  const [channels, setChannels] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const [sales, options] = await Promise.all([fetchSalesDaily({ page: 1, size: 15 }), fetchMetaOptions()]);
    setRows(sales.data);
    setChannels(options.data.channels);
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void load();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>AI OPS</div>
        <nav>
          {SIDE_MENUS.map((menu) => (
            <Link key={menu.label} href={menu.href} className={menu.href === "/sales" ? styles.menuActive : styles.menu}>
              {menu.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <input className={styles.search} placeholder="판매현황 검색" />
          <div className={styles.topActions}><span>🔔</span><span>admin ▾</span></div>
        </header>

        <main className={styles.page}>
          <section className={styles.sectionCard}>
            <header className={styles.header}><h1>판매 현황</h1><Link href="/">← 대시보드</Link></header>
            <form
              className={styles.panel}
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                await upsertSalesDaily({
                  sales_date: String(fd.get("sales_date") || today),
                  channel: String(fd.get("channel") || "ALL"),
                  order_count: Number(fd.get("order_count") || 0),
                  item_qty: Number(fd.get("item_qty") || 0),
                  gross_sales: Number(fd.get("gross_sales") || 0),
                  discount_amount: Number(fd.get("discount_amount") || 0),
                });
                setMessage("판매현황 저장 완료");
                await load();
              }}
            >
              <div className={styles.formGrid}>
                <label className={styles.field}>판매일자<input name="sales_date" type="date" defaultValue={today} required /></label>
                <label className={styles.field}>채널<select name="channel">{channels.map((c) => <option key={c}>{c}</option>)}</select></label>
                <label className={styles.field}>주문건수<input name="order_count" type="number" min={0} defaultValue={10} /></label>
                <label className={styles.field}>판매수량<input name="item_qty" type="number" min={0} defaultValue={25} /></label>
                <label className={styles.field}>총매출<input name="gross_sales" type="number" min={0} defaultValue={200000} /></label>
                <label className={styles.field}>할인금액<input name="discount_amount" type="number" min={0} defaultValue={10000} /></label>
              </div>
              <div className={styles.actions}><button className={styles.primaryBtn}>저장</button></div>
            </form>
            {message ? <p>{message}</p> : null}
          </section>

          <section className={styles.sectionCard}>
            <h2>최근 판매 데이터</h2>
            <div className={styles.panel}>
              <table className={styles.table}>
                <thead><tr><th>일자</th><th>채널</th><th>주문</th><th>수량</th><th>총매출</th><th>할인</th><th>순매출</th></tr></thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={`${r.sales_date}-${r.channel}`}>
                      <td>{r.sales_date}</td><td>{r.channel}</td><td>{r.order_count}</td><td>{r.item_qty}</td>
                      <td>{r.gross_sales.toLocaleString()}</td><td>{r.discount_amount.toLocaleString()}</td><td>{r.net_sales.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
