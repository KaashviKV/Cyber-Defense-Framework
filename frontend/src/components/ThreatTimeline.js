import { formatDateTime } from "../utils/formatters";

function buildEvents(analysis) {
  if (!analysis) return [];

  if (Array.isArray(analysis.audit_trail) && analysis.audit_trail.length) {
    const baseTime = analysis.timestamp ? new Date(analysis.timestamp) : new Date();
    return analysis.audit_trail.map((item, index) => ({
      time: new Date(baseTime.getTime() + index * 1000),
      label: `${item.step}: ${item.detail}`,
      tone: item.step === "fail_safe" ? "warn" : "info",
    }));
  }

  const baseTime = analysis.timestamp ? new Date(analysis.timestamp) : new Date();
  const events = [
    {
      time: new Date(baseTime.getTime() - 120000),
      label: `${analysis.prediction?.attack || "Traffic"} detected`,
      tone: "warn",
    },
    {
      time: new Date(baseTime.getTime() - 60000),
      label: `Risk assessed as ${analysis.risk?.risk_level || "—"} (${analysis.risk?.risk_score ?? "—"})`,
      tone: "danger",
    },
    {
      time: baseTime,
      label: `RL action: ${analysis.decision?.action || "—"}`,
      tone: "info",
    },
  ];

  if (analysis.saved_to_mongodb !== false) {
    events.push({
      time: new Date(baseTime.getTime() + 1000),
      label: "Stored in MongoDB",
      tone: "safe",
    });
  }

  return events;
}

export default function ThreatTimeline({ analysis, history = [] }) {
  const events = analysis
    ? buildEvents(analysis)
    : history.slice(0, 6).flatMap((row) =>
        buildEvents(row).map((event) => ({
          ...event,
          ip: row.ip_address,
        }))
      );

  if (!events.length) {
    return <div className="timeline-empty">No timeline events yet.</div>;
  }

  return (
    <div className="threat-timeline">
      {events.map((event, index) => (
        <div key={`${event.label}-${index}`} className={`timeline-item timeline-${event.tone}`}>
          <div className="timeline-dot" />
          <div className="timeline-content">
            <time>{formatDateTime(event.time)}</time>
            <p>
              {event.ip ? <span className="mono">{event.ip} · </span> : null}
              {event.label}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
