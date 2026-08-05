import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  changePassword as changePasswordRequest,
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  updateProfile as updateProfileRequest,
  type ChangePasswordInput,
  type LoginInput,
  type RegisterInput,
  type UpdateProfileInput,
  type AuthUser,
} from "../services/authService";
import {
  AuthContext,
  type AuthContextValue,
} from "./auth-context";

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

  const updateProfile = useCallback(
    async (
      input: UpdateProfileInput,
    ) => {
      const updatedUser =
        await updateProfileRequest(
          input,
        );

      setUser(updatedUser);

      return updatedUser;
    },
    [],
  );

  const changePassword = useCallback(
    async (
      input: ChangePasswordInput,
    ) => {
      return changePasswordRequest(
        input,
      );
    },
    [],
  );

  const logout = useCallback(
    async () => {
      try {
        await logoutRequest();
      } finally {
        setUser(null);
      }
    },
    [],
  );

  const value =
    useMemo<AuthContextValue>(
      () => ({
        user,
        isAuthenticated:
          user !== null,
        isInitializing,
        login,
        register,
        updateProfile,
        changePassword,
        logout,
      }),
      [
        user,
        isInitializing,
        login,
        register,
        updateProfile,
        changePassword,
        logout,
      ],
    );

  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;