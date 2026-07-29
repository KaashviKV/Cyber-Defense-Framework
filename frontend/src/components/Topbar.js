import { FiMenu, FiRefreshCw } from "react-icons/fi";
import StatusIndicator from "./StatusIndicator";

export default function Topbar({ online, checking, onToggleSidebar, onRefreshHealth, now }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="icon-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
        >
          <FiMenu />
        </button>
        <div className="topbar-title">
          <strong>Intelligent Cyber Defense Framework</strong>
          <span>SOC Console</span>
        </div>
      </div>
      <div className="topbar-right">
        <StatusIndicator online={online} checking={checking} />
        <span style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>{now}</span>
        <button
          type="button"
          className="icon-btn"
          onClick={onRefreshHealth}
          aria-label="Refresh API health"
          title="Refresh API health"
        >
          <FiRefreshCw />
        </button>
      </div>
    </header>
  );
}
