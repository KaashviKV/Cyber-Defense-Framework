import { useMemo, useState } from "react";
import { FiDownload, FiRefreshCw } from "react-icons/fi";
import ThreatTable from "../components/ThreatTable";
import SearchBar from "../components/SearchBar";
import LoadingSpinner from "../components/LoadingSpinner";
import { useHistory } from "../hooks/useHistory";
import { ATTACK_CLASSES, RISK_LEVELS, ACTIONS } from "../utils/constants";
import { exportHistoryToCsv, getActionLabel } from "../utils/formatters";

const PAGE_SIZE = 20;

export default function History() {
  const [skip, setSkip] = useState(0);
  const [ipQuery, setIpQuery] = useState("");
  const [attack, setAttack] = useState("");
  const [risk, setRisk] = useState("");
  const [action, setAction] = useState("");

  const { history, total, loading, error, mongoDown, refresh } = useHistory({
    limit: 200,
    skip: 0,
  });

  const [country, setCountry] = useState("");

  const countries = useMemo(() => {
    const set = new Set();
    history.forEach((row) => {
      const value = row.abuseipdb?.country;
      if (value) set.add(value);
    });
    return Array.from(set).sort();
  }, [history]);

  const filtered = useMemo(() => {
    return history.filter((row) => {
      const ipOk = !ipQuery || String(row.ip_address || "").includes(ipQuery.trim());
      const attackOk = !attack || row.prediction?.attack === attack;
      const riskOk = !risk || row.risk?.risk_level === risk;
      const actionOk = !action || row.decision?.action === action;
      const countryOk = !country || row.abuseipdb?.country === country;
      return ipOk && attackOk && riskOk && actionOk && countryOk;
    });
  }, [history, ipQuery, attack, risk, action, country]);

  const pageRows = filtered.slice(skip, skip + PAGE_SIZE);
  const maxSkip = Math.max(0, filtered.length - PAGE_SIZE);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Threat History</h2>
          <p>Searchable archive of pipeline analyses stored in MongoDB.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={refresh}>
            <FiRefreshCw /> Refresh
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => exportHistoryToCsv(filtered)}
            disabled={!filtered.length}
          >
            <FiDownload /> Export CSV
          </button>
        </div>
      </div>

      {mongoDown && (
        <div className="alert alert-warning">
          MongoDB is unavailable. Start MongoDB on localhost:27017 to load history.
        </div>
      )}
      {error && !mongoDown && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div style={{ flex: "1 1 220px" }}>
          <SearchBar
            value={ipQuery}
            onChange={(v) => {
              setIpQuery(v);
              setSkip(0);
            }}
            placeholder="Search IP…"
            ariaLabel="Search IP"
          />
        </div>
        <select
          className="select"
          style={{ flex: "1 1 180px" }}
          value={attack}
          onChange={(e) => {
            setAttack(e.target.value);
            setSkip(0);
          }}
          aria-label="Filter attack"
        >
          <option value="">All attacks</option>
          {ATTACK_CLASSES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select
          className="select"
          style={{ flex: "1 1 150px" }}
          value={risk}
          onChange={(e) => {
            setRisk(e.target.value);
            setSkip(0);
          }}
          aria-label="Filter risk"
        >
          <option value="">All risk levels</option>
          {RISK_LEVELS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select
          className="select"
          style={{ flex: "1 1 140px" }}
          value={country}
          onChange={(e) => {
            setCountry(e.target.value);
            setSkip(0);
          }}
          aria-label="Filter country"
        >
          <option value="">All countries</option>
          {countries.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select
          className="select"
          style={{ flex: "1 1 180px" }}
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setSkip(0);
          }}
          aria-label="Filter action"
        >
          <option value="">All actions</option>
          {ACTIONS.map((item) => (
            <option key={item} value={item}>
              {getActionLabel(item)}
            </option>
          ))}
        </select>
      </div>

      <div className="chips">
        <span className="chip active">Loaded: {history.length}</span>
        <span className="chip">Server total: {total}</span>
        <span className="chip">Filtered: {filtered.length}</span>
      </div>

      {loading ? (
        <LoadingSpinner label="Loading threat history…" />
      ) : (
        <>
          <ThreatTable
            rows={pageRows}
            emptyTitle="No matching threats"
            emptyMessage="Adjust filters or run a new analysis."
          />
          <div className="pagination">
            <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Showing {filtered.length === 0 ? 0 : skip + 1}–
              {Math.min(skip + PAGE_SIZE, filtered.length)} of {filtered.length}
            </span>
            <div className="page-actions">
              <button
                type="button"
                className="btn btn-outline"
                disabled={skip <= 0}
                onClick={() => setSkip((s) => Math.max(0, s - PAGE_SIZE))}
              >
                Previous
              </button>
              <button
                type="button"
                className="btn btn-outline"
                disabled={skip >= maxSkip}
                onClick={() => setSkip((s) => Math.min(maxSkip, s + PAGE_SIZE))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
