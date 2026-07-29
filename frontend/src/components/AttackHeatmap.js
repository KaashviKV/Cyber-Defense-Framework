import { useMemo } from "react";
import { CHART_PALETTE } from "../utils/constants";

const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function AttackHeatmap({ history = [] }) {
  const { attacks, matrix, max } = useMemo(() => {
    const attackSet = new Set();
    const counts = {};

    history.forEach((row) => {
      const attack = row.prediction?.attack || "Unknown";
      const date = new Date(row.timestamp);
      if (Number.isNaN(date.getTime())) return;
      const hour = date.getHours();
      attackSet.add(attack);
      const key = `${attack}|${hour}`;
      counts[key] = (counts[key] || 0) + 1;
    });

    const attacks = Array.from(attackSet).slice(0, 8);
    const matrix = attacks.map((attack) =>
      HOURS.map((hour) => counts[`${attack}|${hour}`] || 0)
    );
    const max = Math.max(1, ...matrix.flat());

    return { attacks, matrix, max };
  }, [history]);

  if (!attacks.length) {
    return <div className="heatmap-empty">Heatmap will appear once analyses are recorded.</div>;
  }

  return (
    <div className="attack-heatmap">
      <div className="heatmap-hours">
        <span />
        {HOURS.filter((h) => h % 4 === 0).map((hour) => (
          <span key={hour} className="heatmap-hour-label">
            {String(hour).padStart(2, "0")}:00
          </span>
        ))}
      </div>
      {attacks.map((attack, rowIdx) => (
        <div key={attack} className="heatmap-row">
          <span className="heatmap-attack-label" title={attack}>
            {attack}
          </span>
          <div className="heatmap-cells">
            {matrix[rowIdx].map((value, hour) => {
              const intensity = value / max;
              const color = CHART_PALETTE[rowIdx % CHART_PALETTE.length];
              return (
                <div
                  key={`${attack}-${hour}`}
                  className="heatmap-cell"
                  title={`${attack} @ ${hour}:00 — ${value} event(s)`}
                  style={{
                    backgroundColor: value
                      ? `${color}${Math.round(30 + intensity * 170).toString(16).padStart(2, "0")}`
                      : "rgba(15,23,42,0.8)",
                  }}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
