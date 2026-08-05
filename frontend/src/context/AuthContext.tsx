import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  type AuthUser,
} from "../services/authService";
import {
  AuthContext,
  type AuthContextValue,
} from "./auth-context";

type LoginInput = {
  email: string;
  password: string;
};

type RegisterInput = {
  displayName: string;
  email: string;
  password: string;
};

type AuthProviderProps = {
  children: ReactNode;
};

function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [
    isInitializing,
    setIsInitializing,
  ] = useState(true);

  useEffect(() => {
    let isCancelled = false;

    async function restoreSession() {
      try {
        const currentUser =
          await getCurrentUser();

        if (!isCancelled) {
          setUser(currentUser);
        }
      } catch {
        if (!isCancelled) {
          setUser(null);
        }
      } finally {
        if (!isCancelled) {
          setIsInitializing(false);
        }
      }
    }

    void restoreSession();

    return () => {
      isCancelled = true;
    };
  }, []);

  const login = useCallback(
    async (input: LoginInput) => {
      const authenticatedUser =
        await loginRequest(input);

      setUser(authenticatedUser);
    },
    [],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      const authenticatedUser =
        await registerRequest(input);

      setUser(authenticatedUser);
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isInitializing,
      login,
      register,
      logout,
    }),
    [
      user,
      isInitializing,
      login,
      register,
      logout,
    ],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;