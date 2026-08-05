import { createContext } from "react";

import type { AuthUser } from "../services/authService";

type LoginInput = {
  email: string;
  password: string;
};

type RegisterInput = {
  displayName: string;
  email: string;
  password: string;
};

export type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (
    input: LoginInput,
  ) => Promise<void>;
  register: (
    input: RegisterInput,
  ) => Promise<void>;
  logout: () => Promise<void>;
};

export const AuthContext =
  createContext<AuthContextValue | null>(
    null,
  );