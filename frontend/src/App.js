import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Analyze from "./pages/Analyze";
import History from "./pages/History";
import Detail from "./pages/Detail";
import ResponseActions from "./pages/ResponseActions";
import Analytics from "./pages/Analytics";
import Architecture from "./pages/Architecture";
import Experiments from "./pages/Experiments";
import Incidents from "./pages/Incidents";
import IncidentDetail from "./pages/IncidentDetail";
import About from "./pages/About";
import ProjectStats from "./pages/ProjectStats";
import NotFound from "./pages/NotFound";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="analyze" element={<Analyze />} />
          <Route path="history" element={<History />} />
          <Route path="history/:id" element={<Detail />} />
          <Route path="actions" element={<ResponseActions />} />
          <Route path="blocked" element={<Navigate to="/actions" replace />} />
          <Route path="isolated" element={<Navigate to="/actions" replace />} />
          <Route path="alerts" element={<Navigate to="/actions" replace />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="architecture" element={<Architecture />} />
          <Route path="experiments" element={<Experiments />} />
          <Route path="incidents" element={<Incidents />} />
          <Route path="incidents/:id" element={<IncidentDetail />} />
          <Route path="model-health" element={<Navigate to="/" replace />} />
          <Route path="project-stats" element={<ProjectStats />} />
          <Route path="about" element={<About />} />
          <Route path="home" element={<Navigate to="/" replace />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
