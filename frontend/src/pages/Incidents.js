import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchIncidents } from "../api/research";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import ActionBadge from "../components/ActionBadge";
import RiskBadge from "../components/RiskBadge";

export default function Incidents() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchIncidents({ limit: 50 })
      .then((data) => {
        if (active) setRows(data.incidents || []);
      })
      .catch(() => {
        if (active) setError("Incidents require MongoDB.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <LoadingSpinner label="Loading incidents…" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Incidents</h2>
          <p>IP sessions aggregated over a 15-minute window. Responses remain simulated.</p>
        </div>
      </div>
      {error && <div className="alert alert-warning">{error}</div>}
      {!rows.length ? (
        <EmptyState title="No incidents yet" message="Run Live Analyze to open an incident." />
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Flows</th>
                <th>Risk</th>
                <th>Response</th>
                <th>Kill chain</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.incident_id}>
                  <td className="mono">
                    <Link to={`/incidents/${row.incident_id}`}>{row.incident_id}</Link>
                  </td>
                  <td>{row.title}</td>
                  <td>{row.flow_count}</td>
                  <td>
                    <RiskBadge level={row.severity} /> {row.current_risk ?? "—"}
                  </td>
                  <td>
                    <ActionBadge action={row.current_response} />
                  </td>
                  <td>
                    {(row.kill_chain_view || [])
                      .filter((s) => s.active)
                      .map((s) => s.stage)
                      .join(" → ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
