import { useEffect, useState } from "react";
import { FiPlay, FiRefreshCw, FiTrash2, FiZap } from "react-icons/fi";
import { analyzeTraffic } from "../api/analyze";
import { getApiErrorMessage } from "../api/client";
import { fetchHealth } from "../api/research";
import AnalysisResults from "../components/AnalysisResults";
import PipelineVisualization from "../components/PipelineVisualization";
import { useToast } from "../components/Toast";
import { DEMO_ATTACK_IPS, PIPELINE_STAGES } from "../utils/constants";
import { generateDemoFeatures, parseFeatureInput } from "../utils/formatters";
import { pickDemoAttackVector } from "../utils/demoVectors";

export default function Analyze() {
  const { push } = useToast();
  const [ip, setIp] = useState("8.8.8.8");
  const [featuresText, setFeaturesText] = useState("");
  const [validationError, setValidationError] = useState("");
  const [loading, setLoading] = useState(false);
  const [stageIndex, setStageIndex] = useState(-1);
  const [result, setResult] = useState(null);
  const [requestError, setRequestError] = useState("");
  const [demoMeta, setDemoMeta] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let active = true;
    fetchHealth()
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch(() => {
        if (active) setHealth(null);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!loading) return undefined;
    setStageIndex(0);
    const id = setInterval(() => {
      setStageIndex((prev) => (prev < PIPELINE_STAGES.length - 1 ? prev + 1 : prev));
    }, 750);
    return () => clearInterval(id);
  }, [loading]);

  const analysis = result?.analysis;
  const services = health?.services || {};
  const ctiMissing =
    services.virustotal_api === "missing" || services.abuseipdb_api === "missing";
  const mongoStatus = String(services.mongodb || "");
  const mongoDown =
    mongoStatus &&
    !["connected", "ok", "up", "healthy"].includes(mongoStatus.toLowerCase());

  const handleGenerate = () => {
    const values = generateDemoFeatures();
    setFeaturesText(JSON.stringify(values));
    setValidationError("");
    setDemoMeta({ kind: "features" });
    push("Loaded a real CICIDS2017 demo feature vector (78 values).", "success");
  };

  const handleDemoAttack = async () => {
    const pick = DEMO_ATTACK_IPS[Math.floor(Math.random() * DEMO_ATTACK_IPS.length)];
    const sample = pickDemoAttackVector();
    const values = sample?.features ? [...sample.features] : generateDemoFeatures();
    setIp(pick.ip);
    setFeaturesText(JSON.stringify(values));
    setValidationError("");
    setRequestError("");
    setResult(null);
    setDemoMeta({ kind: "attack", attackLabel: sample?.label, ipLabel: pick.label });
    push(
      `Demo attack prepared: ${sample?.label || "attack"} features + ${pick.label} (${pick.ip})`,
      "info"
    );

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
    setDemoMeta(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setRequestError("");
    setResult(null);
    setDemoMeta(null);

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

  return (
    <div className="analyze-page">
      <div className="page-header">
        <div>
          <h2>Live Analyze</h2>
          <p>Run CICIDS → RF → CTI → risk → DQN. Responses are simulated (no live firewall).</p>
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

      {ctiMissing && (
        <div className="alert alert-warning" style={{ marginBottom: "0.85rem" }}>
          CTI API keys are not fully configured. Analysis still runs using ML + risk; set keys in{" "}
          <code>backend/.env</code> for live VirusTotal / AbuseIPDB enrichment.
        </div>
      )}
      {mongoDown && (
        <div className="alert alert-warning" style={{ marginBottom: "0.85rem" }}>
          MongoDB status: <code>{mongoStatus}</code>. History may not persist.
        </div>
      )}

      <form className="card analyze-workspace" onSubmit={handleSubmit}>
        <div className="analyze-workspace-top">
          <div className="field analyze-ip-field">
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

          <div className="analyze-workspace-actions">
            <button type="button" className="btn btn-secondary" onClick={handleGenerate} disabled={loading}>
              <FiRefreshCw /> Load Demo Features
            </button>
            <button type="button" className="btn btn-outline" onClick={handleClear} disabled={loading}>
              <FiTrash2 /> Clear
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <FiPlay /> {loading ? "Running…" : "Run Analysis"}
            </button>
          </div>
        </div>

        <div className="field">
          <label htmlFor="features">Features (exactly 78 CICIDS values)</label>
          <textarea
            id="features"
            className="textarea analyze-features-textarea"
            value={featuresText}
            onChange={(e) => setFeaturesText(e.target.value)}
            placeholder="Paste JSON array, or use Demo Attack / Load Demo Features"
          />
        </div>

        {validationError && (
          <div className="alert alert-error" style={{ marginTop: "0.75rem" }}>
            {validationError}
          </div>
        )}
        {requestError && (
          <div className="alert alert-error" style={{ marginTop: "0.75rem" }}>
            {requestError}
          </div>
        )}

        <div className="analyze-pipeline-block">
          <div className="analyze-pipeline-label">
            <span>Defense pipeline</span>
            {loading ? <em>Running…</em> : analysis ? <em>Complete</em> : <em>Idle</em>}
          </div>
          <PipelineVisualization
            variant="rail"
            stageIndex={stageIndex}
            loading={loading}
            complete={Boolean(analysis) && !loading}
          />
        </div>
      </form>

      {analysis && (
        <div className="analyze-results-wrap">
          <AnalysisResults
            analysis={analysis}
            showPipeline={false}
            pipelineStageIndex={stageIndex}
            pipelineLoading={loading}
            demoMeta={demoMeta}
          />
        </div>
      )}
    </div>
  );
}
