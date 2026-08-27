import { useMemo } from "react";

const HOURS = Array.from({ length: 24 }, (_, i) => i);

function shortAttack(name) {
  if (!name) return "Unknown";
  return name.replace("Web Attack – ", "Web ").replace("DoS ", "DoS ");
}

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
      <p className="heatmap-caption">
        Attack class by hour of day (local time). Darker cells mean more events.
      </p>
      <div className="heatmap-scroll">
        <div className="heatmap-row heatmap-axis">
          <span className="heatmap-attack-label" aria-hidden="true" />
          <div className="heatmap-cells">
            {HOURS.map((hour) => (
              <span key={hour} className="heatmap-hour-tick">
                {hour % 6 === 0 ? String(hour).padStart(2, "0") : ""}
              </span>
            ))}
          </div>
        </div>
        {attacks.map((attack, rowIdx) => (
          <div key={attack} className="heatmap-row">
            <span className="heatmap-attack-label" title={attack}>
              {shortAttack(attack)}
            </span>
            <div className="heatmap-cells">
              {matrix[rowIdx].map((value, hour) => {
                const intensity = value / max;
                return (
                  <div
                    key={`${attack}-${hour}`}
                    className="heatmap-cell"
                    title={`${attack} at ${String(hour).padStart(2, "0")}:00 — ${value} event(s)`}
                    style={{
                      backgroundColor: value
                        ? `rgba(249, 115, 22, ${0.18 + intensity * 0.82})`
                        : "rgba(15, 23, 42, 0.9)",
                    }}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="heatmap-legend" aria-hidden="true">
        <span>Fewer</span>
        <span className="heatmap-legend-bar" />
        <span>More</span>
      </div>
    </div>
  );
}
