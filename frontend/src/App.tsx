import {
  Route,
  Routes,
} from "react-router-dom";

import ProtectedRoute from "./components/auth/ProtectedRoute";
import PublicOnlyRoute from "./components/auth/PublicOnlyRoute";
import AppShell from "./components/layout/AppShell";
import AnalysisPage from "./pages/AnalysisPage";
import ComparePage from "./pages/ComparePage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import NewAnalysisPage from "./pages/NewAnalysisPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProcessingPage from "./pages/ProcessingPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";

function renderProtectedPage(
  page: React.ReactNode,
) {
  return (
    <ProtectedRoute>
      <AppShell>
        {page}
      </AppShell>
    </ProtectedRoute>
  );
}

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<LandingPage />}
      />

      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />

      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <RegisterPage />
          </PublicOnlyRoute>
        }
      />

      <Route
        path="/dashboard"
        element={renderProtectedPage(
          <DashboardPage />,
        )}
      />

      <Route
        path="/analysis/new"
        element={renderProtectedPage(
          <NewAnalysisPage />,
        )}
      />

      <Route
        path="/analysis/processing"
        element={renderProtectedPage(
          <ProcessingPage />,
        )}
      />

      <Route
        path="/analysis/:swingId"
        element={renderProtectedPage(
          <AnalysisPage />,
        )}
      />

      <Route
        path="/history"
        element={renderProtectedPage(
          <HistoryPage />,
        )}
      />

      <Route
        path="/compare"
        element={renderProtectedPage(
          <ComparePage />,
        )}
      />

      <Route
        path="/profile"
        element={renderProtectedPage(
          <ProfilePage />,
        )}
      />

      <Route
        path="*"
        element={<NotFoundPage />}
      />
    </Routes>
  );
}

export default App;