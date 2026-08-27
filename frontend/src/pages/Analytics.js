import { useMemo } from "react";
import { FiDownload, FiRefreshCw } from "react-icons/fi";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import {
  ActionChart,
  AttackChart,
  ConfidenceRiskScatter,
  CountryChart,
  RiskChart,
  SeverityHistogram,
  TrendChart,
} from "../components/Charts";
import { useHistory } from "../hooks/useHistory";
import { exportHistoryToCsv } from "../utils/formatters";
import { exportAnalysisJson } from "../utils/exports";

export default function Analytics() {
  const { history, loading, error, mongoDown, refresh } = useHistory({ limit: 200 });

  const summary = useMemo(() => {
    const attacks = {};
    const maliciousAttacks = {};
    const countries = {};
    let severitySum = 0;
    let confidenceSum = 0;
    let count = 0;

    history.forEach((row) => {
      const attack = row.prediction?.attack || "Unknown";
      attacks[attack] = (attacks[attack] || 0) + 1;
      if (attack !== "BENIGN") {
        maliciousAttacks[attack] = (maliciousAttacks[attack] || 0) + 1;
      }
      const country = row.abuseipdb?.country;
      if (country) countries[country] = (countries[country] || 0) + 1;
      if (row.prediction?.severity != null) {
        severitySum += Number(row.prediction.severity);
        count += 1;
      }
      if (row.prediction?.confidence != null) {
        confidenceSum += Number(row.prediction.confidence);
      }
    });

    const topAttack = Object.entries(maliciousAttacks).sort((a, b) => b[1] - a[1])[0]
      || Object.entries(attacks).sort((a, b) => b[1] - a[1])[0];
    const topCountry = Object.entries(countries).sort((a, b) => b[1] - a[1])[0];

    return {
      topAttack: topAttack ? `${topAttack[0]} (${topAttack[1]})` : "—",
      topCountry: topCountry ? `${topCountry[0]} (${topCountry[1]})` : "—",
      avgSeverity: count ? (severitySum / count).toFixed(1) : "—",
      avgConfidence: count ? (confidenceSum / count).toFixed(1) : "—",
      dailyAnalyses: history.length,
    };
  }, [history]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Analytics</h2>
          <p>Splunk-style distributions, trends, and threat intelligence insights.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={refresh}>
            <FiRefreshCw /> Refresh
          </button>
          <button
            type="button"
            className="btn btn-outline"
            disabled={!history.length}
            onClick={() => exportHistoryToCsv(history)}
          >
            <FiDownload /> Export CSV
          </button>
          <button
            type="button"
            className="btn btn-outline"
            disabled={!history.length}
            onClick={() => exportAnalysisJson({ exported_at: new Date().toISOString(), history })}
          >
            <FiDownload /> Export JSON
          </button>
        </div>
      </div>

      {mongoDown && (
        <div className="alert alert-warning">
          MongoDB is unavailable. Charts will populate once history is accessible.
        </div>
      )}
      {error && !mongoDown && <div className="alert alert-error">{error}</div>}

      {!loading && history.length > 0 && (
        <div className="grid grid-4" style={{ marginBottom: "1rem" }}>
          <div className="card stat-card">
            <span>Top Attack Type</span>
            <strong>{summary.topAttack}</strong>
          </div>
          <div className="card stat-card">
            <span>Top Country (Abuse)</span>
            <strong>{summary.topCountry}</strong>
          </div>
          <div className="card stat-card">
            <span>Avg Severity / Confidence</span>
            <strong>
              {summary.avgSeverity} / {summary.avgConfidence}%
            </strong>
          </div>
          <div className="card stat-card">
            <span>Analyses Loaded</span>
            <strong>{summary.dailyAnalyses}</strong>
          </div>
        </div>
      )}

      {loading ? (
        <LoadingSpinner label="Building analytics…" />
      ) : history.length === 0 ? (
        <EmptyState
          title="No analytics data"
          message="Run analyses to unlock charts and distributions."
        />
      ) : (
        <div className="grid grid-2">
          <div className="card">
            <h3 className="card-title">Analyses Over Time</h3>
            <TrendChart history={history} />
          </div>
          <div className="card">
            <h3 className="card-title">Threat Level Distribution</h3>
            <RiskChart history={history} />
          </div>
          <div className="card">
            <h3 className="card-title">Top Attack Types</h3>
            <AttackChart history={history} />
          </div>
          <div className="card">
            <h3 className="card-title">RL Action Breakdown</h3>
            <ActionChart history={history} />
          </div>
          <div className="card" style={{ gridColumn: "1 / -1" }}>
            <h3 className="card-title">Confidence vs Risk</h3>
            <ConfidenceRiskScatter history={history} />
          </div>
          <div className="card">
            <h3 className="card-title">Countries with Highest Abuse Reports</h3>
            <CountryChart history={history} />
          </div>
          <div className="card">
            <h3 className="card-title">Threat Severity Histogram</h3>
            <SeverityHistogram history={history} />
          </div>
        </div>
      )}
    </div>
  );
}
