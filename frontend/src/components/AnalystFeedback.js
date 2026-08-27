import { useState } from "react";
import { submitAnalysisFeedback } from "../api/research";
import { getApiErrorMessage } from "../api/client";
import { getRecordId } from "../utils/formatters";

const VERDICTS = [
  { id: "correct", label: "Correct response" },
  { id: "too_aggressive", label: "Too aggressive" },
  { id: "too_lenient", label: "Too lenient" },
  { id: "incorrect", label: "Incorrect" },
];

export default function AnalystFeedback({ analysis, onUpdated }) {
  const id = getRecordId(analysis) || analysis?.analysis_id;
  const existing = analysis?.analyst_feedback;
  const [notes, setNotes] = useState(existing?.notes || "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  if (!id) {
    return (
      <p style={{ color: "var(--text-muted)", margin: 0 }}>
        Save this analysis to MongoDB to attach feedback for later model improvement.
      </p>
    );
  }

  async function send(verdict, overrideAction) {
    setSaving(true);
    setMessage("");
    try {
      const data = await submitAnalysisFeedback(id, {
        verdict,
        notes,
        override_action: overrideAction || undefined,
      });
      setMessage(`Recorded: ${verdict.replaceAll("_", " ")}`);
      if (onUpdated && data.analysis) onUpdated(data.analysis);
    } catch (err) {
      setMessage(getApiErrorMessage(err, "Could not save feedback."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="analyst-feedback">
      <p style={{ color: "var(--text-muted)", marginTop: 0 }}>
        Analyst review is stored on the analysis document and can be used by
        <code> scripts/finetune_dqn_from_mongo.py</code>. This does not retrain automatically.
      </p>
      {existing?.verdict && (
        <div className="chip" style={{ marginBottom: "0.75rem" }}>
          Last verdict: {existing.verdict.replaceAll("_", " ")}
        </div>
      )}
      <div className="chips" style={{ marginBottom: "0.75rem" }}>
        {VERDICTS.map((item) => (
          <button
            key={item.id}
            type="button"
            className="btn btn-outline"
            disabled={saving}
            onClick={() => send(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="chips" style={{ marginBottom: "0.75rem" }}>
        {["NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"].map((action) => (
          <button
            key={action}
            type="button"
            className="btn btn-outline"
            disabled={saving}
            onClick={() => send("override", action)}
          >
            Override → {action}
          </button>
        ))}
      </div>
      <textarea
        className="input"
        rows={2}
        placeholder="Optional notes"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
      {message && <p style={{ marginBottom: 0 }}>{message}</p>}
    </div>
  );
}
