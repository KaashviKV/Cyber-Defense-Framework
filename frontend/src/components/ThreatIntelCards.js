import { FiGlobe, FiShield } from "react-icons/fi";
import { formatPercent, getCtiErrorMessage, hasCtiError } from "../utils/formatters";
import SectionHeader from "./SectionHeader";

function StatPill({ label, value, tone = "default" }) {
  return (
    <div className={`cti-pill cti-pill-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function ThreatIntelCards({ virustotal, abuseipdb }) {
  return (
    <div className="grid grid-2">
      <div className="card cti-card">
        <SectionHeader icon={FiShield} title="VirusTotal Intelligence" subtitle="Global reputation scan" />
        {hasCtiError(virustotal) ? (
          <div className="alert alert-warning">{getCtiErrorMessage(virustotal, "virustotal")}</div>
        ) : (
          <div className="cti-grid">
            <StatPill label="Malicious" value={virustotal.malicious} tone="danger" />
            <StatPill label="Suspicious" value={virustotal.suspicious} tone="warn" />
            <StatPill label="Harmless" value={virustotal.harmless} tone="safe" />
            <StatPill label="Undetected" value={virustotal.undetected} tone="info" />
          </div>
        )}
      </div>

      <div className="card cti-card">
        <SectionHeader icon={FiGlobe} title="AbuseIPDB Reputation" subtitle="Community abuse reports" />
        {hasCtiError(abuseipdb) ? (
          <div className="alert alert-warning">{getCtiErrorMessage(abuseipdb, "abuseipdb")}</div>
        ) : (
          <>
            <div className="cti-grid">
              <StatPill label="Country" value={abuseipdb.country || "—"} tone="info" />
              <StatPill label="Confidence" value={formatPercent(abuseipdb.abuse_confidence)} tone="warn" />
              <StatPill label="Reports" value={abuseipdb.total_reports ?? "—"} tone="danger" />
              <StatPill label="Usage Type" value={abuseipdb.usage_type || "—"} tone="default" />
            </div>
            <div className="stat-row" style={{ marginTop: "0.5rem" }}>
              <span>Whitelisted</span>
              <strong>{String(abuseipdb.is_whitelisted)}</strong>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
