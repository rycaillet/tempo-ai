import type {
  NextFunction,
  Request,
  Response,
} from "express";

import { env } from "../config/env.js";

const SAFE_METHODS = new Set([
  "GET",
  "HEAD",
  "OPTIONS",
]);

export function requireTrustedOrigin(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  if (
    SAFE_METHODS.has(request.method)
  ) {
    next();
    return;
  }

  const origin =
    request.get("origin");

  if (!origin) {
    if (
      env.NODE_ENV === "production"
    ) {
      response.status(403).json({
        message:
          "The request origin could not be verified.",
      });

      return;
    }

    next();
    return;
  }

  if (origin !== env.CLIENT_URL) {
    response.status(403).json({
      message:
        "The request origin is not allowed.",
    });

    return;
  }

  next();
}