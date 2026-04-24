"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import styles from "@/app/admin-shell.module.css";
import { createProduct, fetchMetaOptions } from "@/lib/api";

const SIDE_MENUS = [
  { label: "Dashboard", href: "/" },
  { label: "상품 등록", href: "/products/new" },
  { label: "주문/배송", href: "/purchase-orders" },
  { label: "스케줄", href: "/schedule" },
  { label: "판매 현황", href: "/sales" },
];

export default function ProductNewPage() {
  const [options, setOptions] = useState<{ categories: string[]; units: string[]; warehouses: Array<{ id: number; name: string }> }>({
    categories: [],
    units: [],
    warehouses: [],
  });
  const [msg, setMsg] = useState("");

  useEffect(() => {
    fetchMetaOptions().then((res) => {
      setOptions({
        categories: res.data.categories,
        units: res.data.units,
        warehouses: res.data.warehouses,
      });
    });
  }, []);

  async function onSubmit(formData: FormData) {
    setMsg("");
    try {
      await createProduct({
        sku: String(formData.get("sku") || ""),
        name: String(formData.get("name") || ""),
        category: String(formData.get("category") || "기타"),
        unit: String(formData.get("unit") || "ea"),
        safety_stock: Number(formData.get("safety_stock") || 0),
        reorder_point: Number(formData.get("reorder_point") || 0),
        warehouse_id: Number(formData.get("warehouse_id") || 1),
        initial_qty: Number(formData.get("initial_qty") || 0),
      });
      setMsg("상품이 저장되었습니다.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "저장 실패");
    }
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>AI OPS</div>
        <nav>
          {SIDE_MENUS.map((menu) => (
            <Link key={menu.label} href={menu.href} className={menu.href === "/products/new" ? styles.menuActive : styles.menu}>
              {menu.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <input className={styles.search} placeholder="상품 검색" />
          <div className={styles.topActions}><span>🔔</span><span>admin ▾</span></div>
        </header>
        <main className={styles.page}>
          <section className={styles.sectionCard}>
            <header className={styles.header}><h1>상품 등록</h1><Link href="/">← 대시보드</Link></header>
            <form
              className={styles.panel}
              onSubmit={async (event) => {
                event.preventDefault();
                await onSubmit(new FormData(event.currentTarget));
              }}
            >
              <div className={styles.formGrid}>
                <label className={styles.field}>SKU<input name="sku" required /></label>
                <label className={styles.field}>상품명<input name="name" required /></label>
                <label className={styles.field}>카테고리<select name="category">{options.categories.map((c) => <option key={c}>{c}</option>)}</select></label>
                <label className={styles.field}>단위<select name="unit">{options.units.map((u) => <option key={u}>{u}</option>)}</select></label>
                <label className={styles.field}>안전재고<input name="safety_stock" type="number" min={0} defaultValue={0} /></label>
                <label className={styles.field}>재주문점<input name="reorder_point" type="number" min={0} defaultValue={0} /></label>
                <label className={styles.field}>창고<select name="warehouse_id">{options.warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
                <label className={styles.field}>초기 재고<input name="initial_qty" type="number" min={0} defaultValue={0} /></label>
              </div>
              <div className={styles.actions}><button className={styles.primaryBtn} type="submit">저장</button></div>
            </form>
            {msg ? <p>{msg}</p> : null}
          </section>
        </main>
      </div>
    </div>
  );
}
