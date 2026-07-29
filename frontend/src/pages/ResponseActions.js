import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FiRefreshCw } from "react-icons/fi";
import ThreatTable from "../components/ThreatTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { useHistory } from "../hooks/useHistory";
import { ACTIONS } from "../utils/constants";
import { getActionLabel } from "../utils/formatters";

const TABS = [
  {
    key: "BLOCK_IP",
    label: "Blocked IPs",
    description: "IPs where the RL agent recommended blocking traffic.",
    emptyTitle: "No blocked IPs",
    emptyMessage: "Run analyses with high-risk traffic to populate this view.",
  },
  {
    key: "ALERT_ADMIN",
    label: "Alerts",
    description: "Events flagged for administrator review.",
    emptyTitle: "No alerts",
    emptyMessage: "Medium-risk events will appear here when ALERT_ADMIN is chosen.",
  },
  {
    key: "ISOLATE_HOST",
    label: "Isolated Hosts",
    description: "Hosts where the RL agent recommended network isolation.",
    emptyTitle: "No isolated hosts",
    emptyMessage:
      "ISOLATE_HOST is available in the RL policy but is only chosen for the highest-severity intrusions. Try analyzing high-risk demo traffic.",
  },
];

export default function ResponseActions() {
  const [activeTab, setActiveTab] = useState("BLOCK_IP");
  const { history, loading, error, mongoDown, refresh } = useHistory({ limit: 200 });

  const counts = useMemo(() => {
    const map = {};
    ACTIONS.forEach((action) => {
      map[action] = 0;
    });
    history.forEach((row) => {
      const action = row.decision?.action;
      if (action && map[action] != null) map[action] += 1;
    });
    return map;
  }, [history]);

  const tab = TABS.find((item) => item.key === activeTab) || TABS[0];
  const rows = history.filter((row) => row.decision?.action === activeTab);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Response Actions</h2>
          <p>RL defensive decisions grouped by action type.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={refresh}>
            <FiRefreshCw /> Refresh
          </button>
        </div>
      </div>

      {mongoDown && (
        <div className="alert alert-warning">
          MongoDB is unavailable. This view depends on stored history.
        </div>
      )}
      {error && !mongoDown && <div className="alert alert-error">{error}</div>}

      <div className="action-tabs" role="tablist" aria-label="Response action types">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={activeTab === item.key}
            className={`action-tab${activeTab === item.key ? " active" : ""}`}
            onClick={() => setActiveTab(item.key)}
          >
            {item.label}
            <span className="action-tab-count">{counts[item.key] || 0}</span>
          </button>
        ))}
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <p style={{ margin: 0, color: "var(--text-muted)", lineHeight: 1.55 }}>
          {tab.description}{" "}
          {activeTab === "ISOLATE_HOST" && counts.ISOLATE_HOST === 0 && (
            <>
              <Link to="/analyze">Run a demo attack</Link> with a high-abuse IP to increase the chance
              of stronger RL responses.
            </>
          )}
        </p>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <ThreatTable
          rows={rows}
          emptyTitle={tab.emptyTitle}
          emptyMessage={tab.emptyMessage}
        />
      )}

      <div className="chips" style={{ marginTop: "1rem" }}>
        {ACTIONS.map((action) => (
          <span key={action} className="chip">
            {getActionLabel(action)}: {counts[action] || 0}
          </span>
        ))}
      </div>
    </div>
  );
}
