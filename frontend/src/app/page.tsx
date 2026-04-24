"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";
import {
  fetchInventoryItems,
  fetchKpiSummary,
  type InventoryItem,
  type InventoryItemsResponse,
  type KpiSummaryResponse,
  type StockStatus,
} from "@/lib/api";
import AiAskPanel from "./components/ai-ask-panel";

const numberFormatter = new Intl.NumberFormat("ko-KR");
const currencyFormatter = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

function statusLabel(status: StockStatus): string {
  if (status === "OUT") return "품절";
  if (status === "LOW") return "품절 임박";
  return "정상";
}

function statusClassName(status: StockStatus): string {
  if (status === "OUT") return styles.badgeOut;
  if (status === "LOW") return styles.badgeLow;
  return styles.badgeNormal;
}

function buildRiskItems(items: InventoryItem[]): InventoryItem[] {
  return items
    .filter((item) => item.stock_status === "OUT" || item.stock_status === "LOW")
    .sort((a, b) => {
      const rank = { OUT: 0, LOW: 1, NORMAL: 2 };
      return rank[a.stock_status] - rank[b.stock_status] || a.available_qty - b.available_qty;
    })
    .slice(0, 8);
}

const SIDE_MENUS = [
  { label: "Dashboard", href: "/" },
  { label: "상품 등록", href: "/products/new" },
  { label: "주문/배송", href: "/purchase-orders" },
  { label: "스케줄", href: "/schedule" },
  { label: "판매 현황", href: "/sales" },
  { label: "회원관리", href: "#" },
  { label: "고객문의", href: "#" },
];

export default function Home() {
  const [kpi, setKpi] = useState<KpiSummaryResponse | null>(null);
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([]);
  const [inventoryMeta, setInventoryMeta] = useState<InventoryItemsResponse["meta"]>({
    page: 1,
    size: 10,
    total: 0,
  });
  const [inventoryPage, setInventoryPage] = useState(1);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadKpi() {
      try {
        const kpiResult = await fetchKpiSummary();
        if (cancelled) return;
        setKpi(kpiResult);
      } catch (error) {
        if (cancelled) return;
        setErrorMessage(error instanceof Error ? error.message : "대시보드 데이터를 불러오지 못했습니다.");
      }
    }

    loadKpi();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInventory() {
      try {
        const inventoryResult = await fetchInventoryItems({ page: inventoryPage, size: 10 });
        if (cancelled) return;
        setInventoryItems(inventoryResult.data);
        setInventoryMeta(inventoryResult.meta);
        setErrorMessage(null);
      } catch (error) {
        if (cancelled) return;
        setErrorMessage(
          error instanceof Error
            ? `${error.message} · 백엔드 실행 상태와 API_BASE_URL을 확인하세요.`
            : "재고 데이터를 불러오지 못했습니다.",
        );
      }
    }

    loadInventory();
    return () => {
      cancelled = true;
    };
  }, [inventoryPage]);

  const riskItems = useMemo(() => buildRiskItems(inventoryItems), [inventoryItems]);
  const inventoryTotalPages = Math.max(1, Math.ceil(inventoryMeta.total / inventoryMeta.size));
  const inventoryGroupStart = Math.floor((inventoryPage - 1) / 10) * 10 + 1;
  const inventoryGroupEnd = Math.min(inventoryGroupStart + 9, inventoryTotalPages);
  const inventoryPageNumbers = Array.from(
    { length: inventoryGroupEnd - inventoryGroupStart + 1 },
    (_, idx) => inventoryGroupStart + idx,
  );

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>AI OPS</div>
        <nav>
          {SIDE_MENUS.map((menu) => (
            <Link key={menu.label} href={menu.href} className={menu.href === "/" ? styles.menuActive : styles.menu}>
              {menu.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <input className={styles.search} placeholder="검색 (SKU/상품명/발주번호)" />
          <div className={styles.topActions}>
            <span>🔔</span>
            <span>admin ▾</span>
          </div>
        </header>

        <main className={styles.main}>
          <section className={styles.sectionCard}>
            <div className={styles.sectionHeaderRow}>
              <h1>Dashboard</h1>
              <Link href="/purchase-orders" className={styles.quickButton}>
                발주 관리 →
              </Link>
            </div>
            {errorMessage ? <p className={styles.errorBox}>{errorMessage}</p> : null}

            <div className={styles.kpiGrid}>
              <article className={styles.kpiCard}>
                <h2>총 SKU</h2>
                <strong>{formatNumber(kpi?.data.inventory.total_sku ?? 0)}</strong>
              </article>
              <article className={styles.kpiCard}>
                <h2>가용 재고 합계</h2>
                <strong>{formatNumber(kpi?.data.inventory.total_on_hand_qty ?? 0)}</strong>
              </article>
              <article className={styles.kpiCard}>
                <h2>순매출</h2>
                <strong>{formatCurrency(kpi?.data.sales.net_sales ?? 0)}</strong>
              </article>
              <article className={styles.kpiCard}>
                <h2>발주 지연 건수</h2>
                <strong>{formatNumber(kpi?.data.purchase.overdue_count ?? 0)}</strong>
              </article>
            </div>
          </section>

          <section className={styles.sectionCard}>
            <div className={styles.sectionHeaderRow}>
              <h2>재고 리스트</h2>
              <span className={styles.dim}>최신 업데이트 순</span>
            </div>
            <div className={styles.tableWrap}>
              <table>
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>상품명</th>
                    <th>창고</th>
                    <th className={styles.number}>가용 재고</th>
                    <th className={styles.number}>재주문점</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryItems.length === 0 ? (
                    <tr>
                      <td colSpan={6} className={styles.emptyCell}>
                        표시할 재고 데이터가 없습니다.
                      </td>
                    </tr>
                  ) : (
                    inventoryItems.map((item) => (
                      <tr key={`${item.product_id}-${item.warehouse_id}`}>
                        <td>{item.sku}</td>
                        <td>{item.name}</td>
                        <td>{item.warehouse_name}</td>
                        <td className={styles.number}>{formatNumber(item.available_qty)}</td>
                        <td className={styles.number}>{formatNumber(item.reorder_point)}</td>
                        <td>
                          <span className={`${styles.badge} ${statusClassName(item.stock_status)}`}>
                            {statusLabel(item.stock_status)}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className={styles.pagination}>
              <button
                type="button"
                onClick={() => setInventoryPage(Math.max(1, inventoryGroupStart - 10))}
                disabled={inventoryGroupStart <= 1}
              >
                이전
              </button>
              {inventoryPageNumbers.map((pageNo) => (
                <button
                  key={pageNo}
                  type="button"
                  onClick={() => setInventoryPage(pageNo)}
                  className={pageNo === inventoryPage ? styles.activePageButton : ""}
                >
                  {pageNo}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setInventoryPage(Math.min(inventoryTotalPages, inventoryGroupEnd + 1))}
                disabled={inventoryGroupEnd >= inventoryTotalPages}
              >
                다음
              </button>
            </div>
          </section>

          <section className={styles.sectionCard}>
            <div className={styles.sectionHeaderRow}>
              <h2>재고 위험 위젯</h2>
              <span className={styles.dim}>품절/품절 임박 우선 표시</span>
            </div>
            <div className={styles.riskSummary}>
              <div>
                <span>품절</span>
                <strong>{formatNumber(kpi?.data.inventory.out_of_stock_sku ?? 0)}</strong>
              </div>
              <div>
                <span>품절 임박</span>
                <strong>{formatNumber(kpi?.data.inventory.low_stock_sku ?? 0)}</strong>
              </div>
            </div>
            <ul className={styles.riskList}>
              {riskItems.length === 0 ? (
                <li className={styles.emptyRisk}>현재 위험 재고가 없습니다.</li>
              ) : (
                riskItems.map((item) => (
                  <li key={`risk-${item.product_id}-${item.warehouse_id}`}>
                    <div>
                      <p>{item.name}</p>
                      <small>
                        {item.sku} · {item.warehouse_name}
                      </small>
                    </div>
                    <div className={styles.riskRight}>
                      <span className={`${styles.badge} ${statusClassName(item.stock_status)}`}>
                        {statusLabel(item.stock_status)}
                      </span>
                      <strong>{formatNumber(item.available_qty)}</strong>
                    </div>
                  </li>
                ))
              )}
            </ul>
          </section>

          <AiAskPanel />
        </main>
      </div>
    </div>
  );
}
