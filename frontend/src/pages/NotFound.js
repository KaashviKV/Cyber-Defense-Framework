import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="not-found">
      <div>
        <h2>404 — Page not found</h2>
        <p style={{ color: "var(--text-muted)" }}>
          The requested SOC view does not exist.
        </p>
        <Link to="/" className="btn btn-primary" style={{ marginTop: "1rem" }}>
          Back to Overview
        </Link>
      </div>
    </div>
  );
}
