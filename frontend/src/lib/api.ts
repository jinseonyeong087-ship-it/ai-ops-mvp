const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

export type StockStatus = "NORMAL" | "LOW" | "OUT";

export interface KpiSummaryResponse {
  data: {
    inventory: {
      total_sku: number;
      total_on_hand_qty: number;
      low_stock_sku: number;
      out_of_stock_sku: number;
    };
    purchase: {
      draft_count: number;
      submitted_count: number;
      partial_received_count: number;
      overdue_count: number;
    };
    sales: {
      gross_sales: number;
      net_sales: number;
      order_count: number;
      growth_rate_pct: number;
    };
    logistics: {
      inbound_qty: number;
      outbound_qty: number;
    };
  };
  meta: {
    from: string;
    to: string;
    warehouse_id: number | null;
  };
}

export interface InventoryItem {
  product_id: number;
  sku: string;
  name: string;
  category: string;
  warehouse_id: number;
  warehouse_name: string;
  on_hand_qty: number;
  reserved_qty: number;
  available_qty: number;
  safety_stock: number;
  reorder_point: number;
  stock_status: StockStatus;
  updated_at: string | null;
}

export interface InventoryItemsResponse {
  data: InventoryItem[];
  meta: {
    page: number;
    size: number;
    total: number;
  };
}

function getApiBaseUrl(): string {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.API_BASE_URL;
  return (envBase ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

async function safeFetchJson<T>(path: string): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;

  const response = await fetch(url, {
    cache: "no-store",
    signal: AbortSignal.timeout(7000),
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API 요청 실패 (${response.status}) - ${path}`);
  }

  return (await response.json()) as T;
}

export async function fetchKpiSummary(): Promise<KpiSummaryResponse> {
  return safeFetchJson<KpiSummaryResponse>("/kpi/summary");
}

export async function fetchInventoryItems(params?: {
  page?: number;
  size?: number;
  sort?: "name" | "available_qty" | "updated_at";
  order?: "asc" | "desc";
}): Promise<InventoryItemsResponse> {
  const query = new URLSearchParams({
    page: String(params?.page ?? 1),
    size: String(params?.size ?? 10),
    sort: params?.sort ?? "updated_at",
    order: params?.order ?? "desc",
  });

  return safeFetchJson<InventoryItemsResponse>(`/inventory/items?${query.toString()}`);
}
