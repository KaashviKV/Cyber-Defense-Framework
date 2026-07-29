export const ATTACK_CLASSES = [
  "BENIGN",
  "Bot",
  "PortScan",
  "FTP-Patator",
  "SSH-Patator",
  "DoS Hulk",
  "DoS GoldenEye",
  "DoS Slowhttptest",
  "DoS slowloris",
  "DDoS",
  "Heartbleed",
  "Infiltration",
  "Web Attack – Brute Force",
  "Web Attack – Sql Injection",
  "Web Attack – XSS",
];

export const RISK_LEVELS = ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export const ACTIONS = [
  "NO_ACTION",
  "ALERT_ADMIN",
  "BLOCK_IP",
  "ISOLATE_HOST",
];

export const ACTION_LABELS = {
  NO_ACTION: "Allow Traffic",
  ALERT_ADMIN: "Alert Administrator",
  BLOCK_IP: "Block IP",
  ISOLATE_HOST: "Isolate Host",
};

export const RISK_COLORS = {
  SAFE: "#10B981",
  LOW: "#14B8A6",
  MEDIUM: "#F59E0B",
  HIGH: "#F97316",
  CRITICAL: "#EF4444",
};

export const ACTION_COLORS = {
  NO_ACTION: "#10B981",
  ALERT_ADMIN: "#3B82F6",
  BLOCK_IP: "#EF4444",
  ISOLATE_HOST: "#8B5CF6",
};

export const CHART_PALETTE = [
  "#3B82F6",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#14B8A6",
  "#F97316",
  "#6366F1",
  "#EC4899",
  "#22D3EE",
  "#A3E635",
  "#FB7185",
  "#94A3B8",
  "#EAB308",
  "#2DD4BF",
];

export const FEATURE_COUNT = 78;

export const RISK_WEIGHTS = {
  attack: 0.4,
  confidence: 0.2,
  virustotal: 0.2,
  abuseipdb: 0.2,
};

export const DEMO_ATTACK_IPS = [
  { ip: "185.220.101.1", label: "High abuse Tor exit" },
  { ip: "23.129.64.190", label: "High abuse reports" },
  { ip: "45.146.164.110", label: "Known malicious host" },
  { ip: "8.8.8.8", label: "Benign baseline" },
];

export const PIPELINE_STAGES = [
  { key: "input", label: "Input", description: "IP + 78 network features" },
  { key: "rf", label: "Random Forest", description: "Attack classification" },
  { key: "vt", label: "VirusTotal", description: "Global reputation scan" },
  { key: "abuse", label: "AbuseIPDB", description: "Abuse report lookup" },
  { key: "risk", label: "Risk Engine", description: "Weighted risk scoring" },
  { key: "dqn", label: "DQN", description: "RL policy evaluation" },
  { key: "decision", label: "Decision", description: "Defensive action selection" },
  { key: "mongo", label: "MongoDB", description: "Persist analysis record" },
];
