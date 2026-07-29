export default function EmptyState({ title, message, icon = "∅" }) {
  return (
    <div className="empty-state card">
      <div className="glyph" aria-hidden="true">
        {icon}
      </div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}
