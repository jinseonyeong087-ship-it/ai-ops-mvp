import Link from "next/link";
import styles from "./purchase-orders.module.css";
import { fetchPurchaseOrders, type PurchaseOrderStatus } from "@/lib/api";

const STATUS_LABEL: Record<PurchaseOrderStatus, string> = {
  DRAFT: "작성중",
  SUBMITTED: "제출됨",
  PARTIAL_RECEIVED: "부분입고",
  RECEIVED: "입고완료",
  CANCELED: "취소",
};

const SIDE_MENUS = [
  { label: "Dashboard", href: "/" },
  { label: "상품 등록", href: "/products/new" },
  { label: "주문/배송", href: "/purchase-orders" },
  { label: "스케줄", href: "/schedule" },
  { label: "판매 현황", href: "/sales" },
  { label: "회원관리", href: "#" },
  { label: "고객문의", href: "#" },
];

const amountFormatter = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

export default async function PurchaseOrdersPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam ?? "1") || 1);
  const size = 15;

  const response = await fetchPurchaseOrders({ page, size });
  const totalPages = Math.max(1, Math.ceil(response.meta.total / size));
  const groupStart = Math.floor((page - 1) / 10) * 10 + 1;
  const groupEnd = Math.min(groupStart + 9, totalPages);
  const pageNumbers = Array.from({ length: groupEnd - groupStart + 1 }, (_, idx) => groupStart + idx);

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>AI OPS</div>
        <nav>
          {SIDE_MENUS.map((menu) => (
            <Link
              key={menu.label}
              href={menu.href}
              className={menu.href === "/purchase-orders" ? styles.menuActive : styles.menu}
            >
              {menu.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <input className={styles.search} placeholder="검색 (발주번호/거래처)" />
          <div className={styles.topActions}>
            <span>🔔</span>
            <span>admin ▾</span>
          </div>
        </header>

        <main className={styles.page}>
          <section className={styles.sectionCard}>
            <header className={styles.header}>
              <h1>발주 목록</h1>
              <Link href="/" className={styles.backLink}>
                ← 대시보드
              </Link>
            </header>

            <div className={styles.panel}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>발주번호</th>
                    <th>거래처</th>
                    <th>상태</th>
                    <th>발주일</th>
                    <th>예정일</th>
                    <th className={styles.number}>금액</th>
                    <th>상세</th>
                  </tr>
                </thead>
                <tbody>
                  {response.data.length === 0 ? (
                    <tr>
                      <td colSpan={7} className={styles.emptyCell}>
                        표시할 발주 데이터가 없습니다.
                      </td>
                    </tr>
                  ) : (
                    response.data.map((po) => (
                      <tr key={po.id}>
                        <td>{po.po_number}</td>
                        <td>{po.supplier_name}</td>
                        <td>{STATUS_LABEL[po.status]}</td>
                        <td>{po.order_date ?? "-"}</td>
                        <td>{po.expected_date ?? "-"}</td>
                        <td className={styles.number}>{amountFormatter.format(po.total_amount)}</td>
                        <td>
                          <Link href={`/purchase-orders/${po.id}`} className={styles.detailLink}>
                            보기
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              <div className={styles.pagination}>
                <Link href={`/purchase-orders?page=${Math.max(1, groupStart - 10)}`} aria-disabled={groupStart <= 1}>
                  이전
                </Link>
                {pageNumbers.map((pageNo) => (
                  <Link
                    key={pageNo}
                    href={`/purchase-orders?page=${pageNo}`}
                    className={pageNo === page ? styles.activePage : undefined}
                  >
                    {pageNo}
                  </Link>
                ))}
                <Link
                  href={`/purchase-orders?page=${Math.min(totalPages, groupEnd + 1)}`}
                  aria-disabled={groupEnd >= totalPages}
                >
                  다음
                </Link>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
