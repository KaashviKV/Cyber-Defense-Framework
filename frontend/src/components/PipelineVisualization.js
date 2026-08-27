import { PIPELINE_STAGES } from "../utils/constants";

/**
 * Defense pipeline stages.
 * variant="rail" = compact horizontal chips (Analyze page)
 * variant="list" = vertical steps (default)
 */
export default function PipelineVisualization({
  stageIndex = -1,
  loading = false,
  complete = false,
  variant = "list",
}) {
  const steps = PIPELINE_STAGES.map((stage, idx) => {
    let state = "";
    if (complete) state = "done";
    else if (loading) {
      if (idx < stageIndex) state = "done";
      else if (idx === stageIndex) state = "active";
    }
    return { ...stage, idx, state };
  });

  if (variant === "rail") {
    return (
      <div className="pipeline-rail" aria-live="polite">
        {steps.map((stage, i) => (
          <div key={stage.key} className="pipeline-rail-item">
            <div className={`pipeline-rail-chip ${stage.state}`}>
              <span className="pipeline-rail-num">{stage.idx + 1}</span>
              <span className="pipeline-rail-label">{stage.label}</span>
            </div>
            {i < steps.length - 1 ? <span className="pipeline-rail-arrow" aria-hidden="true" /> : null}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="pipeline-viz" aria-live="polite">
      {steps.map((stage) => (
        <div key={stage.key} className={`pipeline-viz-step ${stage.state}`}>
          <div className="pipeline-viz-icon">{stage.idx + 1}</div>
          <div>
            <strong>{stage.label}</strong>
            <span>{stage.description}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
