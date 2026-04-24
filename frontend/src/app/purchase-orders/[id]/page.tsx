import Link from "next/link";
import { notFound } from "next/navigation";
import styles from "./purchase-order-detail.module.css";
import { fetchPurchaseOrderDetail, type PurchaseOrderStatus } from "@/lib/api";
import ReceiveForm from "./receive-form";

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

export default async function PurchaseOrderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const poId = Number(id);

  if (!Number.isInteger(poId) || poId <= 0) {
    notFound();
  }

  const response = await fetchPurchaseOrderDetail(poId).catch(() => null);
  if (!response) {
    notFound();
  }

  const po = response.data;

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1>{po.po_number}</h1>
          <p>
            {po.supplier_name} · 상태: {STATUS_LABEL[po.status]}
          </p>
        </div>
        <Link href="/purchase-orders" className={styles.backLink}>
          ← 발주 목록
        </Link>
      </header>

      <section className={styles.summary}>
        <div>
          <span>발주일</span>
          <strong>{po.order_date ?? "-"}</strong>
        </div>
        <div>
          <span>입고 예정일</span>
          <strong>{po.expected_date ?? "-"}</strong>
        </div>
        <div>
          <span>총액</span>
          <strong>{amountFormatter.format(po.total_amount)}</strong>
        </div>
        <div>
          <span>창고</span>
          <strong>{po.warehouse_id}</strong>
        </div>
      </section>

      <section className={styles.panel}>
        <h2>입고 처리</h2>
        <ReceiveForm poId={po.id} status={po.status} items={po.items} />
      </section>

      <section className={styles.panel}>
        <h2>발주 품목</h2>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>SKU</th>
              <th>상품명</th>
              <th className={styles.number}>발주수량</th>
              <th className={styles.number}>입고수량</th>
              <th className={styles.number}>단가</th>
              <th className={styles.number}>라인금액</th>
            </tr>
          </thead>
          <tbody>
            {po.items.map((item) => (
              <tr key={item.id}>
                <td>{item.sku}</td>
                <td>{item.name}</td>
                <td className={styles.number}>{item.ordered_qty}</td>
                <td className={styles.number}>{item.received_qty}</td>
                <td className={styles.number}>{amountFormatter.format(item.unit_price)}</td>
                <td className={styles.number}>{amountFormatter.format(item.line_amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
