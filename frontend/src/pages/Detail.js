import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { FiArrowLeft, FiCopy } from "react-icons/fi";
import { fetchHistoryItem } from "../api/history";
import { getApiErrorMessage } from "../api/client";
import AnalysisResults from "../components/AnalysisResults";
import LoadingSpinner from "../components/LoadingSpinner";
import { useToast } from "../components/Toast";
import { copyToClipboard } from "../utils/formatters";

export default function Detail() {
  const { id } = useParams();
  const { push } = useToast();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showJson, setShowJson] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchHistoryItem(id);
        if (active) setAnalysis(data.analysis || null);
      } catch (err) {
        if (active) setError(getApiErrorMessage(err, "Failed to load analysis."));
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [id]);

  if (loading) return <LoadingSpinner label="Loading analysis detail…" />;

  if (error) {
    return (
      <div>
        <Link to="/history" className="btn btn-outline" style={{ marginBottom: "1rem" }}>
          <FiArrowLeft /> Back to History
        </Link>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  if (!analysis) {
    return <div className="alert alert-warning">Analysis not found.</div>;
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Analysis Detail</h2>
          <p className="mono">{id}</p>
        </div>
        <div className="page-actions">
          <Link to="/history" className="btn btn-outline">
            <FiArrowLeft /> Back
          </Link>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={async () => {
              const ok = await copyToClipboard(id);
              push(ok ? "ID copied." : "Copy failed.", ok ? "success" : "error");
            }}
          >
            <FiCopy /> Copy ID
          </button>
        </div>
      </div>

      <AnalysisResults analysis={analysis} />

      <div className="card" style={{ marginTop: "1rem" }}>
        <div className="page-header" style={{ marginBottom: "0.75rem" }}>
          <h3 className="card-title" style={{ margin: 0 }}>
            Raw JSON
          </h3>
          <button type="button" className="btn btn-outline" onClick={() => setShowJson((v) => !v)}>
            {showJson ? "Collapse" : "Expand"}
          </button>
        </div>
        {showJson && (
          <pre className="json-viewer">{JSON.stringify(analysis, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}
