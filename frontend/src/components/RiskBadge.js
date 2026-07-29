import { getRiskColor } from "../utils/formatters";

export default function RiskBadge({ level }) {
  const color = getRiskColor(level);
  return (
    <span
      className="badge"
      style={{
        color,
        background: `${color}22`,
        borderColor: `${color}55`,
      }}
    >
      {level || "UNKNOWN"}
    </span>
  );
}
