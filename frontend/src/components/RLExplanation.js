import { FiCpu } from "react-icons/fi";
import { buildRLExplanation } from "../utils/analysis";
import ActionBadge from "./ActionBadge";

export default function RLExplanation({ analysis }) {
  const { bullets, recommendation, actionLabel } = buildRLExplanation(analysis);

  return (
    <div className="rl-explanation">
      <div style={{ marginBottom: "0.75rem" }}>
        <ActionBadge action={analysis?.decision?.action} large />
        <span className="rl-explanation-action">{actionLabel}</span>
      </div>

      <ul className="rl-explanation-list">
        {bullets.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>

      <div className="rl-explanation-reason">
        <FiCpu aria-hidden="true" />
        <p>{recommendation}</p>
      </div>
    </div>
  );
}
