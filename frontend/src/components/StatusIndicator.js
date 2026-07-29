export default function StatusIndicator({ online, checking }) {
  const state = checking ? "checking" : online ? "online" : "offline";
  const label = checking ? "Checking…" : online ? "API Online" : "API Offline";

  return (
    <div className={`status-indicator ${state}`} aria-live="polite">
      <span className="status-dot" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
