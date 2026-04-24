"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { receivePurchaseOrder, type PurchaseOrderDetailResponse } from "@/lib/api";
import styles from "./receive-form.module.css";

interface Props {
  poId: number;
  status: string;
  items: PurchaseOrderDetailResponse["data"]["items"];
}

export default function ReceiveForm({ poId, status, items }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");

  const receivableItems = items
    .map((item) => ({
      product_id: item.product_id,
      received_qty: Math.max(item.ordered_qty - item.received_qty, 0),
    }))
    .filter((item) => item.received_qty > 0);

  const disabled =
    loading ||
    receivableItems.length === 0 ||
    !["SUBMITTED", "PARTIAL_RECEIVED"].includes(status);

  async function onReceiveClick() {
    setLoading(true);
    setMessage("");

    try {
      await receivePurchaseOrder(poId, receivableItems);
      setMessage("입고 처리가 완료되었습니다.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "입고 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.box}>
      <button type="button" onClick={onReceiveClick} disabled={disabled} className={styles.button}>
        {loading ? "처리 중..." : "잔여 수량 전체 입고 처리"}
      </button>
      {message ? <p className={styles.message}>{message}</p> : null}
    </div>
  );
}
