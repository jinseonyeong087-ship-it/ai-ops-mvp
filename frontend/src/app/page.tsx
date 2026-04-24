import Link from "next/link";
import styles from "./page.module.css";
import {
  fetchInventoryItems,
  fetchKpiSummary,
  type InventoryItem,
  type StockStatus,
} from "@/lib/api";
import AiAskPanel from "./components/ai-ask-panel";

interface DashboardData {
  kpi: Awaited<ReturnType<typeof fetchKpiSummary>> | null;
  inventory: Awaited<ReturnType<typeof fetchInventoryItems>> | null;
  errorMessage: string | null;
}

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
    .slice(0, 6);
}

async function getDashboardData(): Promise<DashboardData> {
  try {
    const [kpi, inventory] = await Promise.all([
      fetchKpiSummary(),
      fetchInventoryItems({ size: 12 }),
    ]);

    return {
      kpi,
      inventory,
      errorMessage: null,
    };
  } catch (error) {
    return {
      kpi: null,
      inventory: null,
      errorMessage:
        error instanceof Error
          ? `${error.message} · 백엔드 실행 상태와 API_BASE_URL을 확인하세요.`
          : "대시보드 데이터를 불러오지 못했습니다.",
    };
  }
}

export default async function Home() {
  const { kpi, inventory, errorMessage } = await getDashboardData();
  const inventoryItems = inventory?.data ?? [];
  const riskItems = buildRiskItems(inventoryItems);

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <header className={styles.header}>
          <div>
            <h1>AI Ops Dashboard</h1>
            <p>핵심 KPI, 재고 현황, 위험 항목을 한 화면에서 확인합니다.</p>
          </div>
          <Link href="/purchase-orders" className={styles.headerLink}>
            발주 관리 →
          </Link>
        </header>

        {errorMessage ? <p className={styles.errorBox}>{errorMessage}</p> : null}

        <section className={styles.kpiGrid} aria-label="KPI 요약">
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
        </section>

        <section className={styles.contentGrid}>
          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <h2>재고 테이블</h2>
              <p>최신 업데이트 순</p>
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
          </article>

          <aside className={styles.panel}>
            <div className={styles.panelHeader}>
              <h2>재고 위험 위젯</h2>
              <p>품절/품절 임박 우선 표시</p>
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
          </aside>
        </section>

        <AiAskPanel />
      </main>
    </div>
  );
}
