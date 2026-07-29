import { RISK_WEIGHTS } from "./constants";
import { formatPercent, getActionLabel, hasCtiError } from "./formatters";

export function computeRiskBreakdown(analysis) {
  const risk = analysis?.risk || {};
  const prediction = analysis?.prediction || {};

  const attackScore = Number(risk.attack_score_used ?? prediction.severity ?? 0);
  const confidence = Number(prediction.confidence ?? 0);
  const vtScore = Number(risk.virustotal_score ?? 0);
  const abuseScore = Number(risk.abuseipdb_score ?? 0);

  const components = [
    {
      key: "attack",
      label: "Attack Severity",
      weight: RISK_WEIGHTS.attack,
      rawScore: attackScore,
      contribution: attackScore * RISK_WEIGHTS.attack,
      color: "#EF4444",
    },
    {
      key: "confidence",
      label: "Model Confidence",
      weight: RISK_WEIGHTS.confidence,
      rawScore: confidence,
      contribution: confidence * RISK_WEIGHTS.confidence,
      color: "#3B82F6",
    },
    {
      key: "virustotal",
      label: "VirusTotal",
      weight: RISK_WEIGHTS.virustotal,
      rawScore: vtScore,
      contribution: vtScore * RISK_WEIGHTS.virustotal,
      color: "#8B5CF6",
    },
    {
      key: "abuseipdb",
      label: "AbuseIPDB",
      weight: RISK_WEIGHTS.abuseipdb,
      rawScore: abuseScore,
      contribution: abuseScore * RISK_WEIGHTS.abuseipdb,
      color: "#F59E0B",
    },
  ];

  const total = components.reduce((sum, item) => sum + item.contribution, 0);

  return {
    components: components.map((item) => ({
      ...item,
      weightLabel: `${Math.round(item.weight * 100)}%`,
      contribution: Number(item.contribution.toFixed(2)),
    })),
    total: Number(total.toFixed(2)),
  };
}

export function buildRLExplanation(analysis) {
  const attack = analysis?.prediction?.attack || "Unknown";
  const severity = analysis?.prediction?.severity;
  const confidence = analysis?.prediction?.confidence;
  const riskScore = analysis?.risk?.risk_score;
  const riskLevel = analysis?.risk?.risk_level;
  const action = analysis?.decision?.action;
  const vt = analysis?.virustotal;
  const abuse = analysis?.abuseipdb;

  const bullets = [
    `Attack classified as ${attack}.`,
    `Severity = ${severity ?? "—"}, Model confidence = ${formatPercent(confidence)}.`,
  ];

  if (!hasCtiError(vt) && Number(vt.malicious) > 0) {
    bullets.push(
      `VirusTotal detected malicious activity (${vt.malicious} malicious, ${vt.suspicious} suspicious).`
    );
  } else if (!hasCtiError(abuse) && Number(abuse.abuse_confidence) >= 50) {
    bullets.push(
      `AbuseIPDB reports ${abuse.total_reports} abuse reports with ${formatPercent(abuse.abuse_confidence)} confidence.`
    );
  }

  bullets.push(`Overall Risk Score = ${riskScore ?? "—"} (${riskLevel || "—"}).`);

  let recommendation = "";
  if (action === "BLOCK_IP") {
    recommendation =
      "RL recommends blocking because high-risk attacks receive higher reward when blocked during training.";
  } else if (action === "ISOLATE_HOST") {
    recommendation =
      "RL recommends host isolation for severe intrusions where containment limits lateral movement.";
  } else if (action === "ALERT_ADMIN") {
    recommendation =
      "RL recommends alerting the administrator to investigate while allowing monitored traffic.";
  } else {
    recommendation =
      "RL recommends allowing traffic because the combined risk score is within the safe operating range.";
  }

  return {
    bullets,
    recommendation,
    actionLabel: getActionLabel(action),
  };
}
