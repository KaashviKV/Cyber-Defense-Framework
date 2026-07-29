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
  const points = history
    .map((row) => ({
      x: Number(row.prediction?.confidence),
      y: Number(row.risk?.risk_score),
    }))
    .filter((p) => !Number.isNaN(p.x) && !Number.isNaN(p.y));

  const data = {
    datasets: [
      {
        label: "Confidence vs Risk",
        data: points,
        backgroundColor: "#8B5CF6",
      },
    ],
  };

  return (
    <div style={{ height: 280 }}>
      <Scatter
        data={data}
        options={{
          ...baseOptions,
          scales: {
            x: {
              title: { display: true, text: "Confidence", color: "#94A3B8" },
              min: 0,
              max: 100,
              ticks: { color: "#94A3B8" },
              grid: { color: "#1F2937" },
            },
            y: {
              title: { display: true, text: "Risk Score", color: "#94A3B8" },
              min: 0,
              max: 100,
              ticks: { color: "#94A3B8" },
              grid: { color: "#1F2937" },
            },
          },
        }}
      />
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
