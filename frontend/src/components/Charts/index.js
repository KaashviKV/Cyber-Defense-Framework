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
  const buckets = {};
  history.forEach((row) => {
    if (!row.timestamp) return;
    const day = new Date(row.timestamp).toLocaleDateString();
    buckets[day] = (buckets[day] || 0) + 1;
  });
  const labels = Object.keys(buckets);
  const data = {
    labels,
    datasets: [
      {
        label: "Threats",
        data: labels.map((l) => buckets[l]),
        borderColor: "#3B82F6",
        backgroundColor: "rgba(59,130,246,0.18)",
        fill: true,
        tension: 0.35,
      },
    ],
  };
  return (
    <div style={{ height: 260 }}>
      <Line
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
