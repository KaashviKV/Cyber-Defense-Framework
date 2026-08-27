import { useNavigate } from "react-router-dom";
import RiskBadge from "./RiskBadge";
import ActionBadge from "./ActionBadge";
import EmptyState from "./EmptyState";
import { formatDateTime, formatPercent, getRecordId, safeGet } from "../utils/formatters";

export default function ThreatTable({ rows, emptyTitle, emptyMessage }) {
  const navigate = useNavigate();

  if (!rows?.length) {
    return (
      <EmptyState
        title={emptyTitle || "No analyses available."}
        message={emptyMessage || "Run a live analysis or wait for history to populate."}
        icon="🛡"
      />
    );
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>IP</th>
            <th>Attack</th>
            <th>Confidence</th>
            <th>VT / Abuse</th>
            <th>Risk</th>
            <th>Action</th>
            <th>Country</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const id = getRecordId(row);
            return (
              <tr
                key={id || `${row.ip_address}-${row.timestamp}`}
                onClick={() => id && navigate(`/history/${id}`)}
                onKeyDown={(e) => {
                  if ((e.key === "Enter" || e.key === " ") && id) {
                    navigate(`/history/${id}`);
                  }
                }}
                tabIndex={0}
                role="link"
              >
                <td>{formatDateTime(row.timestamp)}</td>
                <td className="mono">{row.ip_address || "—"}</td>
                <td>{safeGet(row, "prediction.attack")}</td>
                <td>{formatPercent(safeGet(row, "prediction.confidence", null))}</td>
                <td className="mono">
                  {row.risk?.virustotal_score ?? "—"} / {row.risk?.abuseipdb_score ?? "—"}
                </td>
                <td>
                  <RiskBadge level={safeGet(row, "risk.risk_level", null)} />
                </td>
                <td>
                  <ActionBadge action={safeGet(row, "decision.action", null)} />
                </td>
                <td>
                  {safeGet(row, "abuseipdb.country", "—") === "—" ||
                  row.abuseipdb?.error
                    ? "—"
                    : row.abuseipdb.country}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
