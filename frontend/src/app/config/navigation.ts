export interface NavMenuItem {
  label: string;
  href: string;
}

// 전역 메뉴 단일 소스: 메뉴 추가/순서 변경 시 이 파일만 수정하면 됩니다.
export const NAV_MENU_ITEMS: NavMenuItem[] = [
  { label: "Dashboard", href: "/" },
  { label: "상품 등록", href: "/products/new" },
  { label: "주문/배송", href: "/purchase-orders" },
  { label: "스케줄", href: "/schedule" },
  { label: "판매 현황", href: "/sales" },
  { label: "회원관리", href: "#" },
  { label: "고객문의", href: "#" },
];
