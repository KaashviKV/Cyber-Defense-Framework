import { getRiskColor } from "../utils/formatters";

export default function RiskGauge({ score, level, size = "md" }) {
  const numeric = Number(score);
  const safeScore = Number.isNaN(numeric) ? 0 : Math.min(100, Math.max(0, numeric));
  const color = getRiskColor(level);

  return (
    <div className={`risk-gauge risk-gauge-${size}`} aria-label={`Risk score ${safeScore}, level ${level || "unknown"}`}>
      <div className="risk-gauge-track">
        <div
          className="risk-gauge-fill"
          style={{
            width: `${safeScore}%`,
            background: `linear-gradient(90deg, ${color}88, ${color})`,
          }}
        />
      </div>
      <div className="risk-gauge-meta">
        <strong style={{ color }}>{Number.isNaN(numeric) ? "—" : safeScore.toFixed(1)}</strong>
        <span className="risk-gauge-level">{level || "—"}</span>
      </div>
    </div>
  );
}
