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
            <span>🔔</span>
            <span>admin ▾</span>
          </div>
        </header>

        {children}
      </div>
    </div>
  );
}
