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

const amountFormatter = new Intl.NumberFormat("ko-KR", {
  style: "currency",
  currency: "KRW",
  maximumFractionDigits: 0,
});

export default async function PurchaseOrdersPage() {
  const response = await fetchPurchaseOrders({ size: 30 });

  return (
    <main className={styles.page}>
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
            {response.data.map((po) => (
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
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
