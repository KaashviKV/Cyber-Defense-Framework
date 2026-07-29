export default function LoadingSpinner({ label = "Loading…", small = false }) {
  return (
    <div className={`loading-wrap${small ? " loading-wrap-sm" : ""}`} role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      {label ? <div>{label}</div> : null}
    </div>
  );
}
