export default function SectionHeader({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="section-header">
      <div className="section-header-left">
        {Icon ? <Icon aria-hidden="true" /> : null}
        <div>
          <h3 className="card-title" style={{ margin: 0 }}>
            {title}
          </h3>
          {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
        </div>
      </div>
      {action}
    </div>
  );
}
