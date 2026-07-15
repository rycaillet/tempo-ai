import { Route, Routes } from "react-router-dom";

import ComparePage from "./pages/ComparePage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import NewAnalysisPage from "./pages/NewAnalysisPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/analysis/new" element={<NewAnalysisPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/compare" element={<ComparePage />} />
      <Route path="/profile" element={<ProfilePage />} />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
