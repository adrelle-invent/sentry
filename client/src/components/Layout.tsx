import { useState, useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { routes } from "@/routes/manifest";

import AppLogo from "@/components/AppLogo";
import { isDemoMode } from "@/lib/api";

import {
  LayoutDashboard,
  Database,
  AlertTriangle,
  Bell,
  FileText,
  Sun,
  Moon,
} from "lucide-react";

const NAV_ITEMS = [
  { to: routes.dashboard.path, label: "Dashboard", Icon: LayoutDashboard, end: true },
  { to: routes.events.path, label: "Explorer", Icon: Database },
  { to: routes.issues.path, label: "Issues", Icon: AlertTriangle },
  { to: routes.alerts.path, label: "Alerts", Icon: Bell },
  { to: routes.reports.path, label: "Reports", Icon: FileText },
];

export default function Layout() {
  const [isDark, setIsDark] = useState(() => {
    return (
      document.documentElement.classList.contains("dark") ||
      localStorage.getItem("theme") === "dark"
    );
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark]);

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <div className="app-shell-sidebar">
        <aside className="sidebar">
          <div className="sidebar-header">
            <AppLogo />
            <span className="badge badge-neutral badge-mono hidden lg:inline-flex">
              v0.1.0
            </span>
          </div>

          <div className="sidebar-content">
            <nav aria-label="Primary navigation">
              <ul className="sidebar-menu">
                {NAV_ITEMS.map(({ to, label, Icon, end }) => (
                  <li key={to}>
                    <NavLink
                      to={to}
                      end={end}
                      className={({ isActive }) =>
                        `sidebar-item${isActive ? " active" : ""}`
                      }
                    >
                      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      <span>{label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
          </div>

          <div className="sidebar-footer">
            <button
              onClick={() => setIsDark(!isDark)}
              className="sidebar-item w-full justify-start cursor-pointer border-none bg-transparent text-left"
              type="button"
              aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? (
                <>
                  <Sun className="h-4 w-4 shrink-0" style={{ color: "var(--warning)" }} aria-hidden="true" />
                  <span>Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </aside>
      </div>

      {/* Main content */}
      <div className="app-shell-main">
        <header className="app-shell-header justify-end" role="banner">
          {isDemoMode && (
            <span className="badge badge-warning badge-mono text-[10px] mr-3">
              DEMO MODE
            </span>
          )}
          <span className="flex items-center gap-1.5 text-[10px] font-mono text-neutral-foreground">
            <span
              className="badge-dot badge-dot-success"
              aria-label="System operational"
            />
            Operational
          </span>
        </header>

        <main className="app-shell-content" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
