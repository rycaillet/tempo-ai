import type { ReactNode } from "react";
import {
  Navigate,
  useLocation,
} from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import AuthLoadingScreen from "./AuthLoadingScreen";

type ProtectedRouteProps = {
  children: ReactNode;
};

function ProtectedRoute({
  children,
}: ProtectedRouteProps) {
  const location = useLocation();

  const {
    isAuthenticated,
    isInitializing,
  } = useAuth();

  if (isInitializing) {
    return <AuthLoadingScreen />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        replace
        state={{
          from: location.pathname,
        }}
        to="/login"
      />
    );
  }

  return children;
}

export default ProtectedRoute;