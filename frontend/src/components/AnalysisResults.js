import { FiCpu, FiCopy, FiDatabase, FiShield, FiAlertTriangle } from "react-icons/fi";
import ActionBadge from "./ActionBadge";
import ExportButtons from "./ExportButtons";
import FeatureImportance from "./FeatureImportance";
import PipelineVisualization from "./PipelineVisualization";
import RiskBadge from "./RiskBadge";
import RiskBreakdown from "./RiskBreakdown";
import RiskGauge from "./RiskGauge";
import RLExplanation from "./RLExplanation";
import SectionHeader from "./SectionHeader";
import ThreatIntelCards from "./ThreatIntelCards";
import { useToast } from "./Toast";
import { copyToClipboard, formatNumber, formatPercent } from "../utils/formatters";

/**
 * Dense SOC case view: KPI strip → risk/CTI → RL + features.
 */
export default function AnalysisResults({
  analysis,
  showPipeline = false,
  pipelineStageIndex = -1,
  pipelineLoading = false,
  demoMeta = null,
}) {
  const { push } = useToast();

  if (!analysis) return null;

  const attack = analysis.prediction?.attack || "—";
  const confidence = analysis.prediction?.confidence;
  const riskScore = analysis.risk?.risk_score;
  const riskLevel = analysis.risk?.risk_level;
  const analysisId = analysis.analysis_id || analysis._id;

  return (
    <div className="analysis-results">
      <div className="analysis-case-banner">
        <div className="analysis-case-banner-main">
          <div>
            <p className="analysis-case-kicker">Analysis case</p>
            <h3 className="analysis-case-ip mono">{analysis.ip_address}</h3>
          </div>
          <div className="analysis-case-meta">
            <RiskBadge level={riskLevel} />
            <ActionBadge action={analysis.decision?.action} />
            {analysisId ? (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={async () => {
                  const ok = await copyToClipboard(analysisId);
                  push(ok ? "Analysis ID copied." : "Copy failed.", ok ? "success" : "error");
                }}
              >
                <FiCopy /> ID
              </button>
            ) : null}
          </div>
        </div>
        <ExportButtons analysis={analysis} />
      </div>

      <div className="alert alert-info analysis-case-note">
        {demoMeta?.kind === "attack" ? (
          <>
            Demo: real CICIDS2017 <strong>{demoMeta.attackLabel || "attack"}</strong> features
            {demoMeta.ipLabel ? <> · IP profile “{demoMeta.ipLabel}”</> : null}.{" "}
          </>
        ) : null}
        Responses are <strong>simulated</strong> (logs / SOC state only — not a live firewall).
      </div>

      <div className="analyze-kpi-row">
        <div className="analyze-kpi">
          <span>Attack</span>
          <strong>{attack}</strong>
        </div>
        <div className="analyze-kpi">
          <span>Confidence</span>
          <strong>{formatPercent(confidence)}</strong>
        </div>
        <div className="analyze-kpi">
          <span>Severity</span>
          <strong>{formatNumber(analysis.prediction?.severity)}</strong>
        </div>
        <div className="analyze-kpi">
          <span>Risk score</span>
          <strong>{formatNumber(riskScore, 1)}</strong>
          <em>{riskLevel || "—"}</em>
        </div>
        <div className="analyze-kpi analyze-kpi-action">
          <span>RL action</span>
          <ActionBadge action={analysis.decision?.action} large />
        </div>
      </div>

      {showPipeline && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <SectionHeader icon={FiCpu} title="Defense Pipeline" subtitle="ML → CTI → Risk → DQN" />
          <PipelineVisualization
            variant="rail"
            stageIndex={pipelineStageIndex}
            loading={pipelineLoading}
            complete={!pipelineLoading}
          />
        </div>
      )}

      <div className="analysis-main-grid">
        <div className="card analysis-equal-card">
          <SectionHeader icon={FiAlertTriangle} title="Risk assessment" subtitle="Weighted fusion" />
          <div className="analysis-equal-body">
            <RiskGauge score={riskScore} level={riskLevel} size="md" />
            <RiskBreakdown analysis={analysis} />
          </div>
        </div>

        <div className="card analysis-equal-card">
          <SectionHeader icon={FiShield} title="Prediction" subtitle="Random Forest (CICIDS2017)" />
          <div className="analysis-equal-body analysis-equal-body-spread">
            <div className="prediction-hero">
              <span>Attack class</span>
              <strong>{attack}</strong>
            </div>
            <div className="stat-row">
              <span>Severity</span>
              <strong>{formatNumber(analysis.prediction?.severity)}</strong>
            </div>
            <div className="stat-row">
              <span>Confidence</span>
              <strong>{formatPercent(confidence)}</strong>
            </div>
            <div className="prediction-confidence-bar" aria-hidden="true">
              <div
                className="prediction-confidence-fill"
                style={{
                  width: `${Math.min(100, Math.max(0, Number(confidence) <= 1 ? Number(confidence) * 100 : Number(confidence) || 0))}%`,
                }}
              />
            </div>
            <div className="stat-row">
              <span>Saved to MongoDB</span>
              <strong>{analysis.saved_to_mongodb ? "Yes" : "No"}</strong>
            </div>
            {analysis.mongodb_error ? (
              <div className="alert alert-warning">{analysis.mongodb_error}</div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="analysis-section">
        <ThreatIntelCards virustotal={analysis.virustotal} abuseipdb={analysis.abuseipdb} />
      </div>

      <div className="analysis-main-grid">
        <div className="card analysis-equal-card">
          <SectionHeader icon={FiCpu} title="RL decision" subtitle="DQN response (simulated)" />
          <div className="analysis-equal-body">
            <RLExplanation analysis={analysis} />
          </div>
        </div>
        <div className="card analysis-equal-card">
          <SectionHeader icon={FiDatabase} title="Top features" subtitle="Why this classification?" />
          <div className="analysis-equal-body">
            <FeatureImportance topN={5} instanceFeatures={analysis.explanation?.top_features} />
          </div>
        </div>
      </div>

      {analysis.decision?.fail_safe_applied && (
        <div className="alert alert-warning" style={{ marginTop: "1rem" }}>
          {analysis.decision.fail_safe_reason}
        </div>
      )}
    </div>
  );
}
