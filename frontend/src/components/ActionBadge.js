import { getActionColor, getActionLabel } from "../utils/formatters";

export default function ActionBadge({ action, large = false }) {
  const color = getActionColor(action);
  return (
    <span
      className="badge"
      style={{
        color,
        background: `${color}22`,
        borderColor: `${color}55`,
        fontSize: large ? "0.85rem" : undefined,
        padding: large ? "0.4rem 0.8rem" : undefined,
      }}
    >
      {getActionLabel(action)}
    </span>
  );
}
