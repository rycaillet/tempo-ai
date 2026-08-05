const apiBaseUrl =
  import.meta.env.VITE_API_URL ??
  "http://localhost:5001/api";

export type AuthUser = {
  id: string;
  email: string;
  displayName: string;
  createdAt: string;
  updatedAt: string;
};

export type RegisterInput = {
  displayName: string;
  email: string;
  password: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type UpdateProfileInput = {
  displayName: string;
};

export type ChangePasswordInput = {
  currentPassword: string;
  newPassword: string;
};

type AuthResponse = {
  user: AuthUser;
  message?: string;
};

type MessageResponse = {
  message: string;
};

async function parseResponse<T extends object>(
  response: Response,
): Promise<T> {
  let data: T | { message?: string };

  try {
    data = (await response.json()) as
      | T
      | {
          message?: string;
        };
  } catch {
    throw new Error(
      response.ok
        ? "TempoAI received an invalid server response."
        : "TempoAI could not complete the request.",
    );
  }

  if (!response.ok) {
    const message =
      "message" in data &&
      typeof data.message === "string"
        ? data.message
        : "The authentication request failed.";

    throw new Error(message);
  }

  return data as T;
}

export async function register(
  input: RegisterInput,
): Promise<AuthUser> {
  const response = await fetch(
    `${apiBaseUrl}/auth/register`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );

  const data =
    await parseResponse<AuthResponse>(
      response,
    );

  return data.user;
}

export async function login(
  input: LoginInput,
): Promise<AuthUser> {
  const response = await fetch(
    `${apiBaseUrl}/auth/login`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );

  const data =
    await parseResponse<AuthResponse>(
      response,
    );

  return data.user;
}

export async function getCurrentUser(): Promise<
  AuthUser | null
> {
  const response = await fetch(
    `${apiBaseUrl}/auth/me`,
    {
      cache: "no-store",
      credentials: "include",
    },
  );

  if (response.status === 401) {
    return null;
  }

  const data =
    await parseResponse<AuthResponse>(
      response,
    );

  return data.user;
}

export async function updateProfile(
  input: UpdateProfileInput,
): Promise<AuthUser> {
  const response = await fetch(
    `${apiBaseUrl}/auth/profile`,
    {
      method: "PATCH",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );

  const data =
    await parseResponse<AuthResponse>(
      response,
    );

  return data.user;
}

export async function changePassword(
  input: ChangePasswordInput,
): Promise<string> {
  const response = await fetch(
    `${apiBaseUrl}/auth/change-password`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );

  const data =
    await parseResponse<MessageResponse>(
      response,
    );

  return data.message;
}

export async function logout(): Promise<void> {
  const response = await fetch(
    `${apiBaseUrl}/auth/logout`,
    {
      method: "POST",
      credentials: "include",
    },
  );

  await parseResponse<MessageResponse>(
    response,
  );
}