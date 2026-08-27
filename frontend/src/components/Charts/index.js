import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { useMemo } from "react";
import { Doughnut, Bar, Pie, Line, Scatter } from "react-chartjs-2";
import {
  ACTION_COLORS,
  CHART_PALETTE,
  RISK_COLORS,
} from "../../utils/constants";
import { getActionLabel } from "../../utils/formatters";

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
);

const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: "#E5E7EB",
        boxWidth: 12,
      },
    },
    tooltip: {
      backgroundColor: "#111827",
      titleColor: "#E5E7EB",
      bodyColor: "#E5E7EB",
      borderColor: "#334155",
      borderWidth: 1,
    },
  },
};

function countBy(rows, getter) {
  const map = {};
  rows.forEach((row) => {
    const key = getter(row) || "Unknown";
    map[key] = (map[key] || 0) + 1;
  });
  return map;
}

export function RiskChart({ history }) {
  const counts = countBy(history, (r) => r.risk?.risk_level);
  const labels = Object.keys(counts);
  const data = {
    labels,
    datasets: [
      {
        data: labels.map((l) => counts[l]),
        backgroundColor: labels.map((l) => RISK_COLORS[l] || "#94A3B8"),
        borderWidth: 0,
      },
    ],
  };
  return (
    <div style={{ height: 260 }}>
      <Doughnut data={data} options={baseOptions} />
    </div>
  );
}

export function AttackChart({ history }) {
  const counts = countBy(history, (r) => r.prediction?.attack);
  const labels = Object.keys(counts).slice(0, 10);
  const data = {
    labels,
    datasets: [
      {
        label: "Attacks",
        data: labels.map((l) => counts[l]),
        backgroundColor: CHART_PALETTE,
        borderRadius: 6,
      },
    ],
  };
  return (
    <div style={{ height: 260 }}>
      <Bar
        data={data}
        options={{
          ...baseOptions,
          scales: {
            x: { ticks: { color: "#94A3B8" }, grid: { color: "#1F2937" } },
            y: { ticks: { color: "#94A3B8" }, grid: { color: "#1F2937" }, beginAtZero: true },
          },
        }}
      />
    </div>
  );
}

export function ActionChart({ history }) {
  const counts = countBy(history, (r) => r.decision?.action);
  const labels = Object.keys(counts);
  const data = {
    labels: labels.map(getActionLabel),
    datasets: [
      {
        data: labels.map((l) => counts[l]),
        backgroundColor: labels.map((l) => ACTION_COLORS[l] || "#94A3B8"),
        borderWidth: 0,
      },
    ],
  };
  return (
    <div style={{ height: 260 }}>
      <Pie data={data} options={baseOptions} />
    </div>
  );
}

export function TrendChart({ history }) {
  const { labels, values, bucketLabel } = useMemo(() => {
    const dated = history
      .map((row) => (row.timestamp ? new Date(row.timestamp) : null))
      .filter((date) => date && !Number.isNaN(date.getTime()));

    if (!dated.length) {
      return { labels: [], values: [], bucketLabel: "Analyses" };
    }

    const timestamps = dated.map((date) => date.getTime());
    const spanDays = (Math.max(...timestamps) - Math.min(...timestamps)) / (1000 * 60 * 60 * 24);
    const useHours = spanDays <= 2;

    const buckets = new Map();
    history.forEach((row) => {
      if (!row.timestamp) return;
      const date = new Date(row.timestamp);
      if (Number.isNaN(date.getTime())) return;

      const sortKey = useHours
        ? Math.floor(date.getTime() / (1000 * 60 * 60))
        : Math.floor(date.getTime() / (1000 * 60 * 60 * 24));

      const label = useHours
        ? date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit" })
        : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });

      const existing = buckets.get(sortKey);
      if (existing) {
        existing.count += 1;
      } else {
        buckets.set(sortKey, { label, count: 1 });
      }
    });

    const sorted = Array.from(buckets.entries()).sort((a, b) => a[0] - b[0]);

    return {
      labels: sorted.map(([, value]) => value.label),
      values: sorted.map(([, value]) => value.count),
      bucketLabel: useHours ? "Analyses per hour" : "Analyses per day",
    };
  }, [history]);

  const useBar = labels.length <= 3;
  const maxValue = Math.max(...values, 0);
  const suggestedMax = Math.max(maxValue + 1, 5);

  const data = {
    labels,
    datasets: [
      {
        label: bucketLabel,
        data: values,
        borderColor: "#3B82F6",
        backgroundColor: useBar ? "rgba(59,130,246,0.75)" : "rgba(59,130,246,0.18)",
        fill: !useBar,
        tension: 0.35,
        borderRadius: useBar ? 6 : 0,
        pointRadius: useBar ? 0 : 4,
        pointHoverRadius: useBar ? 0 : 6,
      },
    ],
  };

  const scaleOptions = {
    x: { ticks: { color: "#94A3B8", maxRotation: 45, minRotation: 0 }, grid: { color: "#1F2937" } },
    y: {
      ticks: { color: "#94A3B8", stepSize: maxValue <= 10 ? 1 : undefined },
      grid: { color: "#1F2937" },
      beginAtZero: true,
      suggestedMax,
    },
  };

  if (!labels.length) {
    return <div className="heatmap-empty">No timestamped analyses to chart yet.</div>;
  }

  return (
    <div style={{ height: 260 }}>
      {useBar ? (
        <Bar data={data} options={{ ...baseOptions, scales: scaleOptions }} />
      ) : (
        <Line data={data} options={{ ...baseOptions, scales: scaleOptions }} />
      )}
    </div>
  );
}

export function ConfidenceRiskScatter({ history }) {
  const points = useMemo(() => {
    const buckets = new Map();
    history.forEach((row) => {
      const x = Number(row.prediction?.confidence);
      const y = Number(row.risk?.risk_score);
      if (Number.isNaN(x) || Number.isNaN(y)) return;
      const key = `${Math.round(x)}|${Math.round(y)}`;
      const existing = buckets.get(key);
      if (existing) {
        existing.r += 1;
      } else {
        buckets.set(key, { x, y, r: 1 });
      }
    });
    return Array.from(buckets.values());
  }, [history]);

  if (!points.length) {
    return <div className="heatmap-empty">No confidence/risk pairs to plot yet.</div>;
  }

  const data = {
    datasets: [
      {
        label: "Analyses",
        data: points.map((p) => ({
          x: p.x,
          y: p.y,
          count: p.r,
        })),
        pointRadius: (ctx) => Math.min(12, 4 + (ctx.raw?.count || 1)),
        pointHoverRadius: (ctx) => Math.min(14, 6 + (ctx.raw?.count || 1)),
        backgroundColor: points.map((p) =>
          p.y >= 80 ? "rgba(239, 68, 68, 0.75)" : p.y >= 60 ? "rgba(249, 115, 22, 0.75)" : "rgba(59, 130, 246, 0.7)"
        ),
        borderColor: "rgba(15, 23, 42, 0.35)",
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="scatter-wrap">
      <p className="heatmap-caption">
        Each bubble is one or more analyses. X is model confidence, Y is event risk. Size is how
        many share that point. Blue = lower risk, orange = high, red = critical range.
      </p>
      <div className="scatter-canvas">
        <Scatter
          data={data}
          options={{
            ...baseOptions,
            plugins: {
              ...baseOptions.plugins,
              legend: { display: false },
              tooltip: {
                ...baseOptions.plugins.tooltip,
                callbacks: {
                  label: (ctx) => {
                    const raw = ctx.raw || {};
                    return `Confidence ${Number(raw.x).toFixed(0)} · Risk ${Number(raw.y).toFixed(0)}${
                      raw.count > 1 ? ` · ${raw.count} analyses` : ""
                    }`;
                  },
                },
              },
            },
            layout: { padding: { top: 8, right: 12, bottom: 4, left: 4 } },
            scales: {
              x: {
                title: { display: true, text: "Model confidence (0–100)", color: "#94A3B8", font: { size: 12 } },
                min: 0,
                max: 100,
                ticks: { color: "#94A3B8", stepSize: 20 },
                grid: { color: "rgba(31, 41, 55, 0.85)" },
              },
              y: {
                title: { display: true, text: "Risk score (0–100)", color: "#94A3B8", font: { size: 12 } },
                min: 0,
                max: 100,
                ticks: { color: "#94A3B8", stepSize: 20 },
                grid: { color: "rgba(31, 41, 55, 0.85)" },
              },
            },
          }}
        />
      </div>
    </div>
  );
}

export function CountryChart({ history }) {
  const counts = countBy(history, (r) =>
    r.abuseipdb && !r.abuseipdb.error ? r.abuseipdb.country : null
  );
  delete counts.Unknown;
  const labels = Object.keys(counts).slice(0, 8);
  const data = {
    labels,
    datasets: [
      {
        label: "Countries",
        data: labels.map((l) => counts[l]),
        backgroundColor: CHART_PALETTE,
        borderRadius: 6,
      },
    ],
  };
  return (
    <div style={{ height: 260 }}>
      <Bar
        data={data}
        options={{
          ...baseOptions,
          indexAxis: "y",
          scales: {
            x: { ticks: { color: "#94A3B8" }, grid: { color: "#1F2937" }, beginAtZero: true },
            y: { ticks: { color: "#94A3B8" }, grid: { color: "#1F2937" } },
          },
        }}
      />
    </div>
  );
}

export function SeverityHistogram({ history }) {
  const bins = { "0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0 };
  history.forEach((row) => {
    const s = Number(row.prediction?.severity);
    if (Number.isNaN(s)) return;
    if (s <= 20) bins["0-20"] += 1;
    else if (s <= 40) bins["21-40"] += 1;
    else if (s <= 60) bins["41-60"] += 1;
    else if (s <= 80) bins["61-80"] += 1;
    else bins["81-100"] += 1;
  });
  const labels = Object.keys(bins);
  const data = {
    labels,
    datasets: [
      {
        label: "Severity",
        data: labels.map((l) => bins[l]),
        backgroundColor: "#F59E0B",
        borderRadius: 6,
      },
    ],
  };
  return (
    <div style={{ height: 260 }}>
      <Bar
        data={data}
        options={{
          ...baseOptions,
          scales: {
            x: { ticks: { color: "#94A3B8" }, grid: { color: "#1F2937" } },
            y: { ticks: { color: "#94A3B8" }, grid: { color: "#1F2937" }, beginAtZero: true },
          },
        }}
      />
    </div>
  );
}
