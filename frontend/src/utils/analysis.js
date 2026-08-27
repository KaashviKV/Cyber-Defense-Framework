import { RISK_WEIGHTS } from "./constants";
import { formatPercent, getActionLabel, hasCtiError } from "./formatters";

export function computeRiskBreakdown(analysis) {
  const risk = analysis?.risk || {};
  const prediction = analysis?.prediction || {};
  const colors = {
    attack: "#EF4444",
    confidence: "#3B82F6",
    virustotal: "#8B5CF6",
    abuseipdb: "#F59E0B",
  };

  if (Array.isArray(risk.components) && risk.components.length) {
    const components = risk.components.map((item) => ({
      key: item.key,
      label: item.label,
      weight: Number(item.weight ?? 0),
      rawScore: Number(item.rawScore ?? 0),
      contribution: Number(item.contribution ?? 0),
      color: colors[item.key] || "#94A3B8",
      weightLabel: `${Math.round(Number(item.weight ?? 0) * 100)}%`,
    }));
    const total = components.reduce((sum, item) => sum + item.contribution, 0);
    return { components, total: Number(total.toFixed(2)) };
  }

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
  const backend = analysis?.decision?.explanation;
  const attack = analysis?.prediction?.attack || backend?.state_context?.attack || "Unknown";
  const severity = analysis?.prediction?.severity ?? backend?.state_context?.severity;
  const confidence = analysis?.prediction?.confidence ?? backend?.state_context?.confidence;
  const riskScore = analysis?.risk?.risk_score ?? backend?.state_context?.risk_score;
  const riskLevel = analysis?.risk?.risk_level || backend?.state_context?.risk_level;
  const action = analysis?.decision?.action;
  const vt = analysis?.virustotal;
  const abuse = analysis?.abuseipdb;

  const bullets = [
    `Attack classified as ${attack}.`,
    `Severity = ${severity ?? "—"}, Model confidence = ${formatPercent(confidence)}.`,
  ];

  const vtScore = analysis?.risk?.virustotal_score;
  const abuseScore = analysis?.risk?.abuseipdb_score;
  if (vtScore != null || abuseScore != null) {
    bullets.push(
      `CTI inputs to RL: VirusTotal score = ${vtScore ?? "—"}, AbuseIPDB score = ${abuseScore ?? "—"}.`
    );
  }

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

  const modelVersion = analysis?.decision?.rl_model_version;
  if (modelVersion) {
    bullets.push(`RL policy version = ${modelVersion}.`);
  }

  if (backend?.baseline_rule_action) {
    bullets.push(
      `Rule-based baseline would choose ${backend.baseline_rule_action}` +
        `${backend.agrees_with_rule_baseline ? " (agreement)." : " (policy differs)."}`
    );
  }

  const recommendation = backend?.summary
    ? `${backend.summary} ${backend.caveat || ""}`
    : fallbackRecommendation(action);

  return {
    bullets,
    recommendation,
    actionLabel: getActionLabel(action),
    qRanking: backend?.q_ranking || [],
  };
}

function fallbackRecommendation(action) {
  if (action === "BLOCK_IP") {
    return "Recommended action BLOCK_IP from the current risk/CTI state. This is simulated containment, not a live firewall change.";
  }
  if (action === "ISOLATE_HOST") {
    return "Recommended action ISOLATE_HOST for critical-range risk. Isolation is simulated host containment.";
  }
  if (action === "ALERT_ADMIN") {
    return "Recommended action ALERT_ADMIN: investigate before blocking. Event is logged as a simulated alert.";
  }
  return "Recommended action NO_ACTION: combined risk is in a safe range. Traffic is allowed and logged.";
}
