import { FiShield } from "react-icons/fi";

const STAGES = [
  {
    title: "Detection",
    text: "Random Forest classifies network flows into 15 attack categories using 78 CICIDS2017 features.",
  },
  {
    title: "Cyber Threat Intelligence",
    text: "VirusTotal and AbuseIPDB enrich the suspect IP with global reputation and abuse report data.",
  },
  {
    title: "Risk Assessment",
    text: "A weighted risk engine fuses ML severity, model confidence, and CTI scores into a unified 0–100 risk score.",
  },
  {
    title: "Decision",
    text: "A Deep Q-Network reinforcement learning agent selects the optimal defensive action.",
  },
  {
    title: "Response",
    text: "The decision engine simulates blocking, isolation, or alerting, and persists results to MongoDB.",
  },
];

export default function About() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h2>
            <FiShield style={{ verticalAlign: "middle", marginRight: 8 }} />
            About the Framework
          </h2>
          <p>Intelligent Cyber Defense Framework (ICDF) — adaptive network security platform.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <p style={{ margin: 0, lineHeight: 1.7, color: "var(--text-muted)" }}>
          ICDF combines supervised machine learning, external threat intelligence, a weighted risk
          engine, and reinforcement learning to detect attacks, assess risk, and recommend defensive
          actions in near real time. The React SOC dashboard provides live analysis, history,
          analytics, and explainability for academic demonstrations.
        </p>
      </div>

      <div className="about-pipeline">
        {STAGES.map((stage, index) => (
          <div key={stage.title} className="about-stage">
            <div className="about-stage-index">{index + 1}</div>
            <div>
              <h3>{stage.title}</h3>
              <p>{stage.text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
