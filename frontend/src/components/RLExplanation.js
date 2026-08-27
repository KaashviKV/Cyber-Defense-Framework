import { FiCpu } from "react-icons/fi";
import { buildRLExplanation } from "../utils/analysis";
import ActionBadge from "./ActionBadge";

export default function RLExplanation({ analysis }) {
  const { bullets, recommendation, actionLabel, qRanking } = buildRLExplanation(analysis);

  return (
    <div className="rl-explanation rl-explanation-fill">
      <div className="rl-explanation-top">
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
      {qRanking?.length > 0 && (
        <div className="q-ranking">
          <strong>Relative Q-values (policy preference, not causal proof)</strong>
          <ul className="rl-explanation-list">
            {qRanking.map((row) => (
              <li key={row.action}>
                {row.action}: {row.q_value}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
