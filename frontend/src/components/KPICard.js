export default function KPICard({ icon, label, value, description, accent = "#3B82F6" }) {
  return (
    <div className="card kpi-card">
      <div className="kpi-top">
        <div className="kpi-icon" style={{ background: `${accent}22`, color: accent }}>
          {icon}
        </div>
        <span className="kpi-trend">live</span>
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-trend">{description}</div>
    </div>
  );
}
