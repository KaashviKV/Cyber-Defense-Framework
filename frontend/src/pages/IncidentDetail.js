import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchIncident } from "../api/research";
import LoadingSpinner from "../components/LoadingSpinner";
import ActionBadge from "../components/ActionBadge";

export default function IncidentDetail() {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchIncident(id)
      .then((data) => setIncident(data.incident))
      .catch(() => setError("Incident not found or MongoDB is down."));
  }, [id]);

  if (!incident && !error) return <LoadingSpinner />;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div>
      <Link to="/incidents" className="btn btn-outline" style={{ marginBottom: "1rem" }}>
        Back
      </Link>
      <h2>{incident.incident_id}</h2>
      <p>{incident.title}</p>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <div className="stat-row">
          <span>Flows</span>
          <strong>{incident.flow_count}</strong>
        </div>
        <div className="stat-row">
          <span>Current response</span>
          <ActionBadge action={incident.current_response} />
        </div>
        <div className="stat-row">
          <span>Disposition</span>
          <strong>{incident.disposition}</strong>
        </div>
      </div>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3 className="card-title">Kill chain</h3>
        <div className="chips">
          {(incident.kill_chain_view || []).map((stage) => (
            <span key={stage.stage} className={`chip${stage.active ? " active" : ""}`}>
              {stage.stage}
            </span>
          ))}
        </div>
      </div>
      <div className="card">
        <h3 className="card-title">Risk history</h3>
        <pre className="json-viewer">{JSON.stringify(incident.risk_history || [], null, 2)}</pre>
      </div>
    </div>
  );
}
