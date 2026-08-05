import type {
  NextFunction,
  Request,
  Response,
} from "express";
import { z } from "zod";

import {
  getClearSessionCookieOptions,
  getSessionCookieOptions,
  revokeSession,
} from "../auth/session.js";
import { env } from "../config/env.js";
import { HttpError } from "../lib/http-error.js";
import type { AuthenticatedLocals } from "../middleware/require-auth.middleware.js";
import {
  loginUser,
  registerUser,
} from "../services/auth.service.js";

const emailSchema = z
  .string()
  .trim()
  .email("Enter a valid email address.")
  .max(
    254,
    "Email address is too long.",
  );

const registrationPasswordSchema = z
  .string()
  .min(
    12,
    "Password must be at least 12 characters.",
  )
  .max(
    128,
    "Password must be 128 characters or fewer.",
  );

const registerSchema = z.object({
  email: emailSchema,

  displayName: z
    .string()
    .trim()
    .min(
      2,
      "Display name must be at least 2 characters.",
    )
    .max(
      80,
      "Display name must be 80 characters or fewer.",
    ),

  password: registrationPasswordSchema,
});

const loginSchema = z.object({
  email: emailSchema,

  password: z
    .string()
    .min(
      1,
      "Enter your password.",
    )
    .max(
      128,
      "Password must be 128 characters or fewer.",
    ),
});

function parseRequestBody<T>(
  schema: z.ZodType<T>,
  body: unknown,
): T {
  const result = schema.safeParse(body);

  if (!result.success) {
    const firstIssue =
      result.error.issues[0];

    throw new HttpError(
      400,
      firstIssue?.message ??
        "The submitted account information is invalid.",
      result.error.flatten().fieldErrors,
    );
  }

  return result.data;
}

async function revokeExistingSession(
  request: Request,
): Promise<void> {
  const existingToken =
    request.cookies?.[
      env.SESSION_COOKIE_NAME
    ];

  if (
    typeof existingToken === "string" &&
    existingToken.length > 0
  ) {
    await revokeSession(existingToken);
  }
}

export async function registerHandler(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  try {
    const input = parseRequestBody(
      registerSchema,
      request.body,
    );

    await revokeExistingSession(request);

    const result =
      await registerUser(input);

    response.cookie(
      env.SESSION_COOKIE_NAME,
      result.sessionToken,
      getSessionCookieOptions(),
    );

    response.status(201).json({
      user: result.user,
    });
  } catch (error) {
    next(error);
  }
}

export async function loginHandler(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  try {
    const input = parseRequestBody(
      loginSchema,
      request.body,
    );

    await revokeExistingSession(request);

    const result =
      await loginUser(input);

    response.cookie(
      env.SESSION_COOKIE_NAME,
      result.sessionToken,
      getSessionCookieOptions(),
    );

    response.status(200).json({
      user: result.user,
    });
  } catch (error) {
    next(error);
  }
}

export async function getCurrentUserHandler(
  _request: Request,
  response: Response<
    unknown,
    AuthenticatedLocals
  >,
) {
  response.status(200).json({
    user: response.locals.authUser,
  });
}

export async function logoutHandler(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  try {
    const sessionToken =
      request.cookies?.[
        env.SESSION_COOKIE_NAME
      ];

    if (
      typeof sessionToken === "string" &&
      sessionToken.length > 0
    ) {
      await revokeSession(sessionToken);
    }

    response.clearCookie(
      env.SESSION_COOKIE_NAME,
      getClearSessionCookieOptions(),
    );

    response.status(200).json({
      message:
        "You have been signed out.",
    });
  } catch (error) {
    next(error);
  }
}