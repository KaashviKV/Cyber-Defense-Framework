import { useMemo } from "react";
import {
  FiActivity,
  FiAlertTriangle,
  FiLock,
  FiRefreshCw,
  FiShield,
  FiSlash,
  FiTrendingUp,
} from "react-icons/fi";
import KPICard from "../components/KPICard";
import ThreatTable from "../components/ThreatTable";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import LiveThreatFeed from "../components/LiveThreatFeed";
import AttackHeatmap from "../components/AttackHeatmap";
import ThreatTimeline from "../components/ThreatTimeline";
import RiskGauge from "../components/RiskGauge";
import {
  ActionChart,
  AttackChart,
  RiskChart,
  TrendChart,
} from "../components/Charts";
import { useHistory } from "../hooks/useHistory";
import { formatNumber, formatPercent } from "../utils/formatters";

export default function Overview() {
  const { history, total, loading, error, mongoDown, refresh } = useHistory({
    limit: 100,
    skip: 0,
  });

  const stats = useMemo(() => {
    const riskScores = history
      .map((h) => Number(h.risk?.risk_score))
      .filter((n) => !Number.isNaN(n));
    const avgRisk = riskScores.length
      ? riskScores.reduce((a, b) => a + b, 0) / riskScores.length
      : 0;
    const highestRisk = riskScores.length ? Math.max(...riskScores) : 0;
    const blocked = history.filter((h) => h.decision?.action === "BLOCK_IP").length;
    const alerts = history.filter((h) => h.decision?.action === "ALERT_ADMIN").length;
    const isolated = history.filter((h) => h.decision?.action === "ISOLATE_HOST").length;
    const critical = history.filter((h) => h.risk?.risk_level === "CRITICAL").length;
    const safeCount = history.filter((h) =>
      ["SAFE", "LOW"].includes(h.risk?.risk_level)
    ).length;
    const safePct = history.length ? (safeCount / history.length) * 100 : 0;
    const confidences = history
      .map((h) => Number(h.prediction?.confidence))
      .filter((n) => !Number.isNaN(n));
    const avgConfidence = confidences.length
      ? confidences.reduce((a, b) => a + b, 0) / confidences.length
      : 0;
    const latestHighRisk = history.find((h) =>
      ["HIGH", "CRITICAL"].includes(h.risk?.risk_level)
    );

    return {
      avgRisk,
      highestRisk,
      blocked,
      alerts,
      isolated,
      critical,
      safePct,
      avgConfidence,
      latestHighRisk,
    };
  }, [history]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>SOC Overview</h2>
          <p>Live threat feed, attack heatmap, and enterprise security telemetry.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={refresh}>
            <FiRefreshCw /> Refresh
          </button>
        </div>
      </div>

      {mongoDown && (
        <div className="alert alert-warning">
          MongoDB is unavailable. History-backed widgets may be empty until the database is online.
        </div>
      )}
      {error && !mongoDown && <div className="alert alert-error">{error}</div>}

      <div className="grid grid-5" style={{ marginBottom: "1rem" }}>
        <KPICard
          icon={<FiShield />}
          label="Total Analyses"
          value={total}
          description="Stored security analyses"
          accent="#3B82F6"
        />
        <KPICard
          icon={<FiTrendingUp />}
          label="Average Risk"
          value={formatNumber(stats.avgRisk, 1)}
          description="Mean risk score"
          accent="#F59E0B"
        />
        <KPICard
          icon={<FiAlertTriangle />}
          label="Highest Risk"
          value={formatNumber(stats.highestRisk, 1)}
          description="Peak recorded score"
          accent="#EF4444"
        />
        <KPICard
          icon={<FiSlash />}
          label="Blocked IPs"
          value={stats.blocked}
          description="BLOCK_IP decisions"
          accent="#F97316"
        />
        <KPICard
          icon={<FiActivity />}
          label="Safe Traffic"
          value={formatPercent(stats.safePct, 0)}
          description="SAFE + LOW risk share"
          accent="#10B981"
        />
      </div>

      <div className="grid grid-3" style={{ marginBottom: "1rem" }}>
        <KPICard
          icon={<FiAlertTriangle />}
          label="Critical Threats"
          value={stats.critical}
          description="CRITICAL risk level"
          accent="#EF4444"
        />
        <KPICard
          icon={<FiLock />}
          label="Isolated Hosts"
          value={stats.isolated}
          description="ISOLATE_HOST decisions"
          accent="#8B5CF6"
        />
        <KPICard
          icon={<FiAlertTriangle />}
          label="Alerts"
          value={stats.alerts}
          description={`Avg confidence ${formatPercent(stats.avgConfidence, 0)}`}
          accent="#3B82F6"
        />
      </div>

      {loading ? (
        <LoadingSpinner label="Loading dashboard telemetry…" />
      ) : history.length === 0 ? (
        <EmptyState
          title="No analyses available."
          message="Run Live Analyze to populate the SOC dashboard."
        />
      ) : (
        <>
          <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
            <div className="card">
              <h3 className="card-title">Live Threat Feed</h3>
              <LiveThreatFeed rows={history} maxItems={10} />
            </div>
            <div className="card">
              <h3 className="card-title">Attack Heatmap</h3>
              <AttackHeatmap history={history} />
            </div>
          </div>

          {stats.latestHighRisk && (
            <div className="card" style={{ marginBottom: "1rem" }}>
              <h3 className="card-title">Current Risk Posture</h3>
              <div className="grid grid-2">
                <RiskGauge
                  score={stats.latestHighRisk.risk?.risk_score}
                  level={stats.latestHighRisk.risk?.risk_level}
                  size="lg"
                />
                <ThreatTimeline analysis={stats.latestHighRisk} />
              </div>
            </div>
          )}

          <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
            <div className="card">
              <h3 className="card-title">Risk Distribution</h3>
              <RiskChart history={history} />
            </div>
            <div className="card">
              <h3 className="card-title">Attack Distribution</h3>
              <AttackChart history={history} />
            </div>
            <div className="card">
              <h3 className="card-title">RL Action Distribution</h3>
              <ActionChart history={history} />
            </div>
            <div className="card">
              <h3 className="card-title">Threats Over Time</h3>
              <TrendChart history={history} />
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Recent Incidents</h3>
            <ThreatTable rows={history.slice(0, 12)} />
          </div>
        </>
      )}
    </div>
  );
}
