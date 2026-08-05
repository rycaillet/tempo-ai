import type {
  NextFunction,
  Request,
  Response,
} from "express";

import {
  resolveSession,
  type AuthenticatedUser,
} from "../auth/session.js";

import { env } from "../config/env.js";

export type AuthenticatedLocals = {
  authUser: AuthenticatedUser;
};

export async function requireAuth(
  request: Request,
  response: Response<
    unknown,
    AuthenticatedLocals
  >,
  next: NextFunction,
) {
  try {
    const cookieValue =
      request.cookies?.[
        env.SESSION_COOKIE_NAME
      ];

    if (
      typeof cookieValue !== "string" ||
      cookieValue.length === 0
    ) {
      response.status(401).json({
        message: "Sign in to continue.",
      });

      return;
    }

    const user =
      await resolveSession(cookieValue);

    if (!user) {
      response.status(401).json({
        message:
          "Your session is no longer valid. Sign in again.",
      });

      return;
    }

    response.locals.authUser = user;

    next();
  } catch (error) {
    next(error);
  }
}