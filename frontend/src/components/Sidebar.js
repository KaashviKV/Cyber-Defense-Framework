import { NavLink } from "react-router-dom";
import {
  FiActivity,
  FiAlertTriangle,
  FiBookOpen,
  FiCpu,
  FiGrid,
  FiShield,
  FiZap,
} from "react-icons/fi";

/** Primary nav for project panel / viva — keep focused. */
const links = [
  { to: "/", label: "Overview", icon: FiGrid, end: true },
  { to: "/analyze", label: "Live Analyze", icon: FiZap },
  { to: "/history", label: "Threat History", icon: FiActivity },
  { to: "/actions", label: "Response Actions", icon: FiAlertTriangle },
  { to: "/experiments", label: "Experiments", icon: FiBookOpen },
  { to: "/architecture", label: "Architecture", icon: FiCpu },
];

export default function Sidebar({ collapsed }) {
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`} aria-label="Primary">
      <div className="sidebar-brand">
        <h1>
          <FiShield style={{ marginRight: 8, verticalAlign: "middle" }} />
          ICDF
        </h1>
        {!collapsed && (
          <p>Adaptive Network Security using RL + Cyber Threat Intelligence</p>
        )}
      </div>
      <nav className="sidebar-nav">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            title={label}
          >
            <Icon aria-hidden="true" />
            <span className="nav-label">{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
