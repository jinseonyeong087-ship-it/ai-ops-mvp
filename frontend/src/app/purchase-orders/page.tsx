import Link from "next/link";
import styles from "./purchase-orders.module.css";
import AppShell from "@/app/components/app-shell";
import { fetchPurchaseOrders, type PurchaseOrderStatus } from "@/lib/api";

const STATUS_LABEL: Record<PurchaseOrderStatus, string> = {
  DRAFT: "작성중",
  SUBMITTED: "제출됨",
  PARTIAL_RECEIVED: "부분입고",
  RECEIVED: "입고완료",
  CANCELED: "취소",
};

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
    <AppShell styles={styles} activeHref="/purchase-orders" searchPlaceholder="검색 (발주번호/거래처)">
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
    </AppShell>
  );
}
