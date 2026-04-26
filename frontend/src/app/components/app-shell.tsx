import Link from "next/link";
import { NAV_MENU_ITEMS } from "@/app/config/navigation";

type StyleModule = Readonly<Record<string, string>>;

export default function AppShell({
  styles,
  activeHref,
  searchPlaceholder,
  children,
}: Readonly<{
  styles: StyleModule;
  activeHref: string;
  searchPlaceholder: string;
  children: React.ReactNode;
}>) {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>AI OPS</div>
        <nav>
          {NAV_MENU_ITEMS.map((menu) => (
            <Link key={menu.label} href={menu.href} className={menu.href === activeHref ? styles.menuActive : styles.menu}>
              {menu.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <input className={styles.search} placeholder={searchPlaceholder} />
          <div className={styles.topActions}>
            <span title="Notifications" aria-label="Notifications" style={{ display: "inline-flex", alignItems: "center" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M15 18H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <path
                  d="M18 16V11C18 7.68629 15.3137 5 12 5C8.68629 5 6 7.68629 6 11V16L4 18H20L18 16Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <span>admin ▼</span>
          </div>
        </header>

        {children}
      </div>
    </div>
  );
}
