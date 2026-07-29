import { Link } from "react-router-dom";
import RiskBadge from "./RiskBadge";
import ActionBadge from "./ActionBadge";
import { formatDateTime, getRecordId } from "../utils/formatters";

export default function LiveThreatFeed({ rows = [], maxItems = 8 }) {
  const items = rows.slice(0, maxItems);

  if (!items.length) {
    return (
      <div className="live-feed empty">
        <p>No live threats yet. Run an analysis to populate the feed.</p>
      </div>
    );
  }

  return (
    <div className="live-feed" aria-live="polite">
      {items.map((row) => {
        const id = getRecordId(row);
        const content = (
          <div className="live-feed-item">
            <div className="live-feed-main">
              <strong className="mono">{row.ip_address}</strong>
              <span>{row.prediction?.attack || "—"}</span>
            </div>
            <div className="live-feed-meta">
              <RiskBadge level={row.risk?.risk_level} />
              <ActionBadge action={row.decision?.action} />
              <span className="live-feed-time">{formatDateTime(row.timestamp)}</span>
            </div>
          </div>
        );

        return id ? (
          <Link key={id} to={`/history/${id}`} className="live-feed-link">
            {content}
          </Link>
        ) : (
          <div key={`${row.ip_address}-${row.timestamp}`} className="live-feed-link">
            {content}
          </div>
        );
      })}
    </div>
  );
}
