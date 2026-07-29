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
      "CTI APIs provide malicious vote counts, abuse confidence, country, and usage type. Results are cached and retried for resilience.",
  },
  {
    id: "risk",
    title: "Risk Engine",
    icon: FiShield,
    summary: "Weighted fusion: Attack 40%, Confidence 20%, VT 20%, AbuseIPDB 20%.",
    details:
      "The risk engine combines ML and CTI signals into a 0–100 score mapped to SAFE, LOW, MEDIUM, HIGH, or CRITICAL levels.",
  },
  {
    id: "dqn",
    title: "Deep Q-Network (DQN)",
    icon: FiCpu,
    summary: "Reinforcement learning agent selects a defensive action.",
    details:
      "The DQN policy maps state vectors (attack, severity, risk) to actions: NO_ACTION, ALERT_ADMIN, BLOCK_IP, or ISOLATE_HOST.",
  },
  {
    id: "mongo",
    title: "MongoDB",
    icon: FiDatabase,
    summary: "Persists full analysis for SOC history, analytics, and audit.",
    details:
      "Each pipeline run stores prediction, CTI, risk, decision, performance timings, and request metadata for dashboard visualization.",
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
