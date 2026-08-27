import { useEffect, useState } from "react";
import { fetchExperiments } from "../api/research";
import LoadingSpinner from "../components/LoadingSpinner";

/**
 * Panel-focused experiments: summary tables only (no raw JSON dumps).
 */
export default function Experiments() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      try {
        const data = await fetchExperiments();
        if (active) setPayload(data);
      } catch (err) {
        if (active) setError("Could not load experiment artifacts.");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <LoadingSpinner label="Loading experiment artifacts…" />;

  const experiments = payload?.experiments || {};
  const compare = experiments.ml_model_comparison?.data?.results;
  const ablation = experiments.response_ablation?.data?.results;
  const unsw = experiments.unsw_nb15_evaluation?.data;
  const unswMetrics = unsw?.metrics;
  const phase4Table = experiments.cross_dataset_phase4?.data?.comparison_table;
  const fprRec = experiments.unsw_nb15_fpr_threshold?.data?.overall_recommendation;
  const fprModels = experiments.unsw_nb15_fpr_threshold?.data?.models;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Experiments</h2>
          <p>
            Key evaluation results for the report and viva. Full JSON artifacts remain under{" "}
            <code>ml/saved_models/</code>.
          </p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {experiments.ml_model_comparison?.data?.dataset === "synthetic_smoke" && (
        <div className="alert alert-warning" style={{ marginBottom: "1rem" }}>
          IDS comparison currently uses synthetic smoke data. Prefer a real CICIDS run for the report.
        </div>
      )}

      {Array.isArray(compare) && compare.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 className="card-title">IDS model comparison (CICIDS2017)</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Accuracy</th>
                  <th>Macro-F1</th>
                  <th>FPR</th>
                  <th>FNR</th>
                </tr>
              </thead>
              <tbody>
                {compare.map((row) => (
                  <tr key={row.model}>
                    <td>{row.model}</td>
                    <td>{row.error ? row.error : row.accuracy}</td>
                    <td>{row.macro_f1 ?? "—"}</td>
                    <td>{row.false_positive_rate ?? "—"}</td>
                    <td>{row.false_negative_rate ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {Array.isArray(ablation) && ablation.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 className="card-title">Response policy: Rule vs DQN vs Double DQN</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Avg reward</th>
                  <th>Correct response</th>
                  <th>Unnecessary blocks</th>
                </tr>
              </thead>
              <tbody>
                {ablation.map((row) => (
                  <tr key={row.name}>
                    <td>{row.name}</td>
                    <td>{row.avg_reward}</td>
                    <td>{row.correct_response_rate ?? "—"}</td>
                    <td>{row.unnecessary_block_rate ?? row.false_block_rate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {unswMetrics && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 className="card-title">UNSW-NB15 standalone RF</h3>
          <p style={{ color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Separate research dataset (not production CICIDS). High attack recall with elevated FPR.
          </p>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Macro-F1</th>
                  <th>Attack recall</th>
                  <th>FPR</th>
                  <th>FNR</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{unswMetrics.macro_f1 ?? "—"}</td>
                  <td>{unswMetrics.attack_recall ?? "—"}</td>
                  <td>{unswMetrics.false_positive_rate ?? "—"}</td>
                  <td>{unswMetrics.false_negative_rate ?? "—"}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {fprRec && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 className="card-title">UNSW FPR threshold tuning</h3>
          <p style={{ color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Raising P(attack) threshold lowers classifier FPR while keeping high recall.
          </p>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>τ</th>
                  <th>Attack recall</th>
                  <th>FPR</th>
                  <th>FPR reduction</th>
                </tr>
              </thead>
              <tbody>
                {(fprModels || []).map((m) => (
                  <tr key={m.model}>
                    <td>{m.model}</td>
                    <td>{m.recommended?.threshold ?? "—"}</td>
                    <td>{m.recommended?.attack_recall ?? "—"}</td>
                    <td>{m.recommended?.false_positive_rate ?? "—"}</td>
                    <td>{m.recommended?.fpr_reduction_vs_baseline ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {Array.isArray(phase4Table) && phase4Table.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 className="card-title">Cross-dataset transfer (aligned)</h3>
          <p style={{ color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Honest result: in-domain works; CICIDS↔UNSW transfer collapses after alignment.
          </p>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Setting</th>
                  <th>Attack recall</th>
                  <th>FPR</th>
                  <th>ROC-AUC</th>
                </tr>
              </thead>
              <tbody>
                {phase4Table.map((row) => (
                  <tr key={row.setting}>
                    <td>{row.setting}</td>
                    <td>{row.attack_recall ?? "—"}</td>
                    <td>{row.false_positive_rate ?? "—"}</td>
                    <td>{row.roc_auc ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
