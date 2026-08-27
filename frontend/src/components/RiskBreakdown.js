import { computeRiskBreakdown } from "../utils/analysis";
import { formatNumber } from "../utils/formatters";

export default function RiskBreakdown({ analysis }) {
  const { components, total } = computeRiskBreakdown(analysis);
  const maxContribution = Math.max(...components.map((item) => item.contribution), 1);

  return (
    <div className="risk-breakdown">
      <div className="risk-breakdown-bar" aria-hidden="true">
        {components.map((item) => (
          <div
            key={item.key}
            className="risk-breakdown-segment"
            style={{
              width: `${(item.contribution / maxContribution) * 100}%`,
              backgroundColor: item.color,
              flexGrow: item.contribution,
            }}
            title={`${item.label}: ${formatNumber(item.contribution, 2)}`}
          />
        ))}
      </div>

      <div className="risk-breakdown-legend">
        {components.map((item) => (
          <div key={item.key} className="risk-breakdown-item">
            <span className="risk-breakdown-dot" style={{ backgroundColor: item.color }} />
            <div>
              <strong>{item.label}</strong>
              <div className="risk-breakdown-sub">
                Weight {item.weightLabel} · Raw {formatNumber(item.rawScore, 1)} · Contrib{" "}
                {formatNumber(item.contribution, 2)}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="stat-row">
        <span>Weighted Total</span>
        <strong>{formatNumber(total, 2)}</strong>
      </div>
    </div>
  );
}
