import { useState } from "react";
import { FiCpu, FiDatabase, FiGlobe, FiShield } from "react-icons/fi";

const NODES = [
  {
    id: "input",
    title: "Network Input",
    icon: FiGlobe,
    summary: "IP address + 78 CICIDS2017 flow features from live or demo traffic.",
    details:
      "The framework accepts a source/destination IP and a 78-dimensional feature vector representing flow statistics such as duration, packet lengths, and flag counts.",
  },
  {
    id: "rf",
    title: "Random Forest",
    icon: FiShield,
    summary: "Supervised classifier predicting one of 15 attack classes.",
    details:
      "A trained Random Forest model classifies traffic into attack types (DDoS, PortScan, Web Attacks, etc.) and outputs severity and confidence scores used downstream.",
  },
  {
    id: "cti",
    title: "Threat Intelligence",
    icon: FiGlobe,
    summary: "VirusTotal and AbuseIPDB enrich the IP with global reputation data.",
    details:
      "CTI APIs provide malicious vote counts, abuse confidence, country, and usage type. Results are cached and retried. If API keys are missing, enrichment is skipped and the risk engine continues with ML signals (unknown CTI, not treated as clean).",
  },
  {
    id: "risk",
    title: "Risk Engine",
    icon: FiShield,
    summary: "Weighted fusion: Attack 40%, Confidence 20%, VT 20%, AbuseIPDB 20%.",
    details:
      "The risk engine combines ML and CTI signals into a 0–100 score mapped to SAFE, LOW, MEDIUM, HIGH, or CRITICAL. Report volume is blended into AbuseIPDB; whitelist scales CTI.",
  },
  {
    id: "xai",
    title: "Explainable AI",
    icon: FiCpu,
    summary: "Local feature attribution for the predicted attack class.",
    details:
      "Each analysis includes leave-one-feature-out importance so an analyst can see why this flow was classified as a given attack, plus global Random Forest importances.",
  },
  {
    id: "dqn",
    title: "Deep Q-Network (DQN)",
    icon: FiCpu,
    summary: "Reinforcement learning agent selects a defensive action.",
    details:
      "The DQN policy maps CTI-aware state vectors to simulated actions. Q-values are shown as relative preference, not human-readable causal reasoning.",
  },
  {
    id: "sim",
    title: "Simulated Response",
    icon: FiShield,
    summary: "Allow, alert, blocklist, or isolate — logged only.",
    details:
      "Actions update a JSON SOC state and log files. Nothing is pushed to a real firewall.",
  },
  {
    id: "mongo",
    title: "MongoDB",
    icon: FiDatabase,
    summary: "Persists full analysis for SOC history, analytics, and audit.",
    details:
      "Each pipeline run stores prediction, CTI, risk, decision, explanation, timings, and optional analyst feedback for fine-tuning.",
  },
];

export default function Architecture() {
  const [active, setActive] = useState("rf");
  const selected = NODES.find((node) => node.id === active) || NODES[1];
  const Icon = selected.icon;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>System Architecture</h2>
          <p>Interactive pipeline diagram for demonstrations and viva Q&amp;A.</p>
        </div>
      </div>

      <div className="architecture-flow">
        {NODES.map((node, index) => {
          const NodeIcon = node.icon;
          return (
            <div key={node.id} className="architecture-flow-item">
              <button
                type="button"
                className={`architecture-node${active === node.id ? " active" : ""}`}
                onClick={() => setActive(node.id)}
              >
                <NodeIcon />
                <span>{node.title}</span>
              </button>
              {index < NODES.length - 1 ? <div className="architecture-arrow">→</div> : null}
            </div>
          );
        })}
      </div>

      <div className="card architecture-detail">
        <div className="section-header">
          <div className="section-header-left">
            <Icon aria-hidden="true" />
            <div>
              <h3 className="card-title" style={{ margin: 0 }}>
                {selected.title}
              </h3>
              <p className="section-subtitle">{selected.summary}</p>
            </div>
          </div>
        </div>
        <p style={{ margin: 0, color: "var(--text-muted)", lineHeight: 1.6 }}>{selected.details}</p>
      </div>
    </div>
  );
}
