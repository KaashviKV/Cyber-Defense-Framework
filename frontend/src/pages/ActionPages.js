import { FiRefreshCw } from "react-icons/fi";
import ThreatTable from "../components/ThreatTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { useHistory } from "../hooks/useHistory";

function FilteredActionPage({ title, subtitle, action, emptyTitle, emptyMessage }) {
  const { history, loading, error, mongoDown, refresh } = useHistory({ limit: 200 });
  const rows = history.filter((row) => row.decision?.action === action);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
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

      {loading ? (
        <LoadingSpinner />
      ) : (
        <ThreatTable rows={rows} emptyTitle={emptyTitle} emptyMessage={emptyMessage} />
      )}
    </div>
  );
}

export function Blocked() {
  return (
    <FilteredActionPage
      title="Blocked IPs"
      subtitle="Hosts where the RL agent recommended BLOCK_IP."
      action="BLOCK_IP"
      emptyTitle="No blocked IPs"
      emptyMessage="No BLOCK_IP decisions in history yet."
    />
  );
}

export function Isolated() {
  return (
    <FilteredActionPage
      title="Isolated Hosts"
      subtitle="Hosts where the RL agent recommended ISOLATE_HOST."
      action="ISOLATE_HOST"
      emptyTitle="No isolated hosts"
      emptyMessage="No ISOLATE_HOST decisions in history yet."
    />
  );
}

export function Alerts() {
  return (
    <FilteredActionPage
      title="Alerts"
      subtitle="Events where the RL agent recommended ALERT_ADMIN."
      action="ALERT_ADMIN"
      emptyTitle="No alerts"
      emptyMessage="No ALERT_ADMIN decisions in history yet."
    />
  );
}
