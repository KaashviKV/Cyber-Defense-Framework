import { FiCpu, FiDatabase, FiShield, FiAlertTriangle } from "react-icons/fi";
import ActionBadge from "./ActionBadge";
import ExportButtons from "./ExportButtons";
import FeatureImportance from "./FeatureImportance";
import PipelineVisualization from "./PipelineVisualization";
import RiskBreakdown from "./RiskBreakdown";
import RiskGauge from "./RiskGauge";
import RLExplanation from "./RLExplanation";
import SectionHeader from "./SectionHeader";
import ThreatIntelCards from "./ThreatIntelCards";
import ThreatTimeline from "./ThreatTimeline";
import { formatDateTime, formatNumber, formatPercent } from "../utils/formatters";

export default function AnalysisResults({
  analysis,
  showPipeline = false,
  pipelineStageIndex = -1,
  pipelineLoading = false,
}) {
  if (!analysis) return null;

  return (
    <div className="analysis-results">
      <div className="page-header" style={{ marginBottom: "1rem" }}>
        <div>
          <h3 style={{ margin: 0 }}>Analysis Results</h3>
          <p className="mono" style={{ margin: "0.25rem 0 0", color: "var(--text-muted)" }}>
            {analysis.ip_address}
          </p>
        </div>
        <ExportButtons analysis={analysis} />
      </div>

      {showPipeline && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <SectionHeader icon={FiCpu} title="Defense Pipeline" subtitle="End-to-end processing stages" />
          <PipelineVisualization
            stageIndex={pipelineStageIndex}
            loading={pipelineLoading}
            complete={!pipelineLoading}
          />
        </div>
      )}

      <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
        <div className="card">
          <SectionHeader icon={FiShield} title="Prediction" subtitle="Random Forest classifier" />
          <div className="stat-row">
            <span>Attack</span>
            <strong>{analysis.prediction?.attack || "—"}</strong>
          </div>
          <div className="stat-row">
            <span>Severity</span>
            <strong>{formatNumber(analysis.prediction?.severity)}</strong>
          </div>
          <div className="stat-row">
            <span>Confidence</span>
            <strong>{formatPercent(analysis.prediction?.confidence)}</strong>
          </div>
        </div>

        <div className="card">
          <SectionHeader icon={FiAlertTriangle} title="Risk Assessment" subtitle="Weighted risk engine" />
          <RiskGauge score={analysis.risk?.risk_score} level={analysis.risk?.risk_level} size="lg" />
          <div style={{ marginTop: "1rem" }}>
            <RiskBreakdown analysis={analysis} />
          </div>
        </div>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <ThreatIntelCards virustotal={analysis.virustotal} abuseipdb={analysis.abuseipdb} />
      </div>

      <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
        <div className="card">
          <SectionHeader icon={FiCpu} title="RL Decision" subtitle="Deep Q-Network recommendation" />
          <RLExplanation analysis={analysis} />
        </div>

        <div className="card">
          <SectionHeader icon={FiDatabase} title="Metadata" subtitle="Persistence and audit trail" />
          <div className="stat-row">
            <span>Timestamp</span>
            <strong>{formatDateTime(analysis.timestamp)}</strong>
          </div>
          <div className="stat-row">
            <span>Action</span>
            <ActionBadge action={analysis.decision?.action} />
          </div>
          <div className="stat-row">
            <span>Saved to MongoDB</span>
            <strong>{analysis.saved_to_mongodb ? "Yes" : "No"}</strong>
          </div>
          <div className="stat-row">
            <span>Analysis ID</span>
            <strong className="mono">{analysis.analysis_id || analysis._id || "—"}</strong>
          </div>
          {analysis.mongodb_error && (
            <div className="alert alert-warning" style={{ marginTop: "0.75rem" }}>
              {analysis.mongodb_error}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <SectionHeader title="Threat Timeline" subtitle="Detection to response sequence" />
          <ThreatTimeline analysis={analysis} />
        </div>
        <div className="card">
          <SectionHeader title="Model Explainability" subtitle="Top Random Forest features" />
          <FeatureImportance topN={5} />
        </div>
      </div>
    </div>
  );
}
