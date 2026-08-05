import { createContext } from "react";

import type {
  AuthUser,
  ChangePasswordInput,
  LoginInput,
  RegisterInput,
  UpdateProfileInput,
} from "../services/authService";

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

  updateProfile: (
    input: UpdateProfileInput,
  ) => Promise<AuthUser>;

  changePassword: (
    input: ChangePasswordInput,
  ) => Promise<string>;

  logout: () => Promise<void>;
};

export const AuthContext =
  createContext<AuthContextValue | null>(
    null,
  );