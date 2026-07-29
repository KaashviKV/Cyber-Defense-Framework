import { useEffect, useMemo, useState } from "react";
import { FiCopy, FiPlay, FiRefreshCw, FiTrash2, FiZap } from "react-icons/fi";
import { analyzeTraffic } from "../api/analyze";
import { getApiErrorMessage } from "../api/client";
import AnalysisResults from "../components/AnalysisResults";
import PipelineVisualization from "../components/PipelineVisualization";
import RiskBadge from "../components/RiskBadge";
import ActionBadge from "../components/ActionBadge";
import { useToast } from "../components/Toast";
import { DEMO_ATTACK_IPS, PIPELINE_STAGES } from "../utils/constants";
import {
  copyToClipboard,
  formatNumber,
  generateDemoFeatures,
  parseFeatureInput,
} from "../utils/formatters";

export default function Analyze() {
  const { push } = useToast();
  const [ip, setIp] = useState("8.8.8.8");
  const [featuresText, setFeaturesText] = useState("");
  const [validationError, setValidationError] = useState("");
  const [loading, setLoading] = useState(false);
  const [stageIndex, setStageIndex] = useState(-1);
  const [result, setResult] = useState(null);
  const [requestError, setRequestError] = useState("");

  useEffect(() => {
    if (!loading) return undefined;
    setStageIndex(0);
    const id = setInterval(() => {
      setStageIndex((prev) => (prev < PIPELINE_STAGES.length - 1 ? prev + 1 : prev));
    }, 750);
    return () => clearInterval(id);
  }, [loading]);

  const analysis = result?.analysis;

  const handleGenerate = () => {
    const values = generateDemoFeatures();
    setFeaturesText(JSON.stringify(values));
    setValidationError("");
    push("Generated 78 demo feature values.", "success");
  };

  const handleDemoAttack = async () => {
    const pick = DEMO_ATTACK_IPS[Math.floor(Math.random() * DEMO_ATTACK_IPS.length)];
    const values = generateDemoFeatures();
    setIp(pick.ip);
    setFeaturesText(JSON.stringify(values));
    setValidationError("");
    setRequestError("");
    setResult(null);
    push(`Demo attack prepared: ${pick.label} (${pick.ip})`, "info");

    setLoading(true);
    try {
      const data = await analyzeTraffic({
        ip_address: pick.ip,
        features: values,
      });
      setResult(data);
      push("Demo attack analysis completed.", "success");
    } catch (err) {
      const message = getApiErrorMessage(err, "Demo analysis failed.");
      setRequestError(message);
      push(message, "error");
    } finally {
      setLoading(false);
      setStageIndex(-1);
    }
  };

  const handleClear = () => {
    setFeaturesText("");
    setValidationError("");
    setResult(null);
    setRequestError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setRequestError("");
    setResult(null);

    if (!ip.trim()) {
      setValidationError("IP address is required.");
      return;
    }

    const parsed = parseFeatureInput(featuresText);
    if (!parsed.ok) {
      setValidationError(parsed.error);
      return;
    }

    setValidationError("");
    setLoading(true);
    try {
      const data = await analyzeTraffic({
        ip_address: ip.trim(),
        features: parsed.values,
      });
      setResult(data);
      push("Security analysis completed.", "success");
    } catch (err) {
      const message = getApiErrorMessage(err, "Analysis failed.");
      setRequestError(message);
      push(message, "error");
    } finally {
      setLoading(false);
      setStageIndex(-1);
    }
  };

  const stageStates = useMemo(() => {
    return PIPELINE_STAGES.map((stage, idx) => {
      if (!loading && analysis) return { label: stage.label, state: "done" };
      if (!loading) return { label: stage.label, state: "" };
      if (idx < stageIndex) return { label: stage.label, state: "done" };
      if (idx === stageIndex) return { label: stage.label, state: "active" };
      return { label: stage.label, state: "" };
    });
  }, [loading, stageIndex, analysis]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Live Analyze</h2>
          <p>Submit network features and IP for end-to-end AI security analysis.</p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleDemoAttack}
            disabled={loading}
          >
            <FiZap /> Generate Demo Attack
          </button>
        </div>
      </div>

      <div className="grid grid-2">
        <form className="card" onSubmit={handleSubmit}>
          <h3 className="card-title">Analysis Request</h3>

          <div className="field" style={{ marginBottom: "0.9rem" }}>
            <label htmlFor="ip">IP Address</label>
            <input
              id="ip"
              className="input"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="e.g. 8.8.8.8"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="features">Features (exactly 78 values)</label>
            <textarea
              id="features"
              className="textarea"
              value={featuresText}
              onChange={(e) => setFeaturesText(e.target.value)}
              placeholder='Paste JSON array [0.1, 0.2, ...] or comma-separated values'
            />
          </div>

          {validationError && (
            <div className="alert alert-error" style={{ marginTop: "0.9rem" }}>
              {validationError}
            </div>
          )}

          <div className="page-actions" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn btn-secondary" onClick={handleGenerate}>
              <FiRefreshCw /> Generate Demo Features
            </button>
            <button type="button" className="btn btn-outline" onClick={handleClear}>
              <FiTrash2 /> Clear
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <FiPlay /> {loading ? "Running…" : "Run Security Analysis"}
            </button>
          </div>

          {(loading || analysis) && (
            <div className="pipeline" aria-live="polite" style={{ marginTop: "1rem" }}>
              {stageStates.map((step) => (
                <div key={step.label} className={`pipeline-step ${step.state}`}>
                  <span>{step.label}</span>
                </div>
              ))}
            </div>
          )}
        </form>

        <div className="card">
          <h3 className="card-title">Pipeline Visualization</h3>
          {loading && (
            <div className="loading-wrap">
              <div className="spinner" />
              <div>Executing AI defense pipeline…</div>
            </div>
          )}
          {!loading && !analysis && !requestError && (
            <div className="empty-state" style={{ padding: "1.5rem 0.5rem" }}>
              <h3>Ready</h3>
              <p>Use Demo Attack or paste a 78-value vector, then run analysis.</p>
            </div>
          )}
          {requestError && <div className="alert alert-error">{requestError}</div>}
          <PipelineVisualization
            stageIndex={stageIndex}
            loading={loading}
            complete={Boolean(analysis) && !loading}
          />
          {analysis && (
            <div style={{ marginTop: "1rem" }}>
              <div className="stat-row">
                <span>IP</span>
                <strong className="mono">{analysis.ip_address}</strong>
              </div>
              <div className="stat-row">
                <span>Attack</span>
                <strong>{analysis.prediction?.attack || "—"}</strong>
              </div>
              <div className="stat-row">
                <span>Risk</span>
                <RiskBadge level={analysis.risk?.risk_level} />
              </div>
              <div className="stat-row">
                <span>Score</span>
                <strong>{formatNumber(analysis.risk?.risk_score, 2)}</strong>
              </div>
              <div className="stat-row">
                <span>Action</span>
                <ActionBadge action={analysis.decision?.action} />
              </div>
              {analysis.analysis_id && (
                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ marginTop: "0.8rem" }}
                  onClick={async () => {
                    const ok = await copyToClipboard(analysis.analysis_id);
                    push(ok ? "Analysis ID copied." : "Copy failed.", ok ? "success" : "error");
                  }}
                >
                  <FiCopy /> Copy Analysis ID
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {analysis && (
        <div style={{ marginTop: "1rem" }}>
          <AnalysisResults
            analysis={analysis}
            showPipeline={false}
            pipelineStageIndex={stageIndex}
            pipelineLoading={loading}
          />
        </div>
      )}
    </div>
  );
}
