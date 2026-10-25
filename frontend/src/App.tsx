import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Knowledge from "./pages/Knowledge";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <div className="shell">
      <nav className="nav">
        <strong>Fire Design Agent</strong>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Projects
        </NavLink>
        <NavLink to="/knowledge" className={({ isActive }) => (isActive ? "active" : "")}>
          Knowledge
        </NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects/:id" element={<Workspace />} />
        <Route path="/knowledge" element={<Knowledge />} />
      </Routes>
    </div>
  );
}
