import { PIPELINE_STAGES } from "../utils/constants";

export default function PipelineVisualization({ stageIndex = -1, loading = false, complete = false }) {
  return (
    <div className="pipeline-viz" aria-live="polite">
      {PIPELINE_STAGES.map((stage, idx) => {
        let state = "";
        if (complete) state = "done";
        else if (loading) {
          if (idx < stageIndex) state = "done";
          else if (idx === stageIndex) state = "active";
        }

        return (
          <div key={stage.key} className={`pipeline-viz-step ${state}`}>
            <div className="pipeline-viz-icon">{idx + 1}</div>
            <div>
              <strong>{stage.label}</strong>
              <span>{stage.description}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
