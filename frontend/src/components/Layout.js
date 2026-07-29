import { useEffect, useMemo, useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { useHealth } from "../hooks/useHealth";
import { ToastProvider } from "./Toast";

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [tick, setTick] = useState(Date.now());
  const { online, checking, refresh } = useHealth();

  useEffect(() => {
    const id = setInterval(() => setTick(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const now = useMemo(
    () =>
      new Date(tick).toLocaleString(undefined, {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }),
    [tick]
  );

  return (
    <ToastProvider>
      <div className="app-shell">
        <Sidebar collapsed={collapsed} />
        <div className="main-area">
          <Topbar
            online={online}
            checking={checking}
            now={now}
            onToggleSidebar={() => setCollapsed((v) => !v)}
            onRefreshHealth={refresh}
          />
          <main className="content">
            <Outlet />
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
