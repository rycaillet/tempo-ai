import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import AuthLoadingScreen from "./AuthLoadingScreen";

type PublicOnlyRouteProps = {
  children: ReactNode;
};

function PublicOnlyRoute({
  children,
}: PublicOnlyRouteProps) {
  const {
    isAuthenticated,
    isInitializing,
  } = useAuth();

  if (isInitializing) {
    return <AuthLoadingScreen />;
  }

  if (isAuthenticated) {
    return (
      <Navigate
        replace
        to="/dashboard"
      />
    );
  }

  return children;
}

export default PublicOnlyRoute;