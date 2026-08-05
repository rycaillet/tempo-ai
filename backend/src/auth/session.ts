import {
  createHash,
  randomBytes,
} from "node:crypto";

import type { CookieOptions } from "express";

import { env } from "../config/env.js";
import { prisma } from "../lib/prisma.js";

const SESSION_TOKEN_BYTES = 32;
const MILLISECONDS_PER_DAY =
  24 * 60 * 60 * 1000;

export type AuthenticatedUser = {
  id: string;
  email: string;
  displayName: string;
  createdAt: Date;
  updatedAt: Date;
};

function hashSessionToken(
  token: string,
): string {
  return createHash("sha256")
    .update(token, "utf8")
    .digest("hex");
}

function createSessionExpiration(): Date {
  return new Date(
    Date.now() +
      env.SESSION_TTL_DAYS *
        MILLISECONDS_PER_DAY,
  );
}

export function getSessionCookieOptions(): CookieOptions {
  return {
    httpOnly: true,
    secure: env.NODE_ENV === "production",
    sameSite: env.SESSION_COOKIE_SAME_SITE,
    path: "/",
    maxAge:
      env.SESSION_TTL_DAYS *
      MILLISECONDS_PER_DAY,
  };
}

export function getClearSessionCookieOptions(): CookieOptions {
  const options =
    getSessionCookieOptions();

  return {
    httpOnly: options.httpOnly,
    secure: options.secure,
    sameSite: options.sameSite,
    path: options.path,
  };
}

export async function createSession(
  userId: string,
): Promise<{
  token: string;
  expiresAt: Date;
}> {
  const token = randomBytes(
    SESSION_TOKEN_BYTES,
  ).toString("base64url");

  const tokenHash =
    hashSessionToken(token);

  const expiresAt =
    createSessionExpiration();

  await prisma.session.create({
    data: {
      tokenHash,
      expiresAt,
      userId,
    },
  });

  return {
    token,
    expiresAt,
  };
}

export async function resolveSession(
  token: string,
): Promise<AuthenticatedUser | null> {
  const tokenHash =
    hashSessionToken(token);

  const session =
    await prisma.session.findUnique({
      where: {
        tokenHash,
      },

      select: {
        id: true,
        expiresAt: true,

        user: {
          select: {
            id: true,
            email: true,
            displayName: true,
            createdAt: true,
            updatedAt: true,
          },
        },
      },
    });

  if (!session) {
    return null;
  }

  if (
    session.expiresAt.getTime() <=
    Date.now()
  ) {
    await prisma.session.delete({
      where: {
        id: session.id,
      },
    });

    return null;
  }

  return session.user;
}

export async function revokeSession(
  token: string,
): Promise<void> {
  const tokenHash =
    hashSessionToken(token);

  await prisma.session.deleteMany({
    where: {
      tokenHash,
    },
  });
}

export async function revokeOtherSessions(
  userId: string,
  currentToken: string,
): Promise<void> {
  const currentTokenHash =
    hashSessionToken(currentToken);

  await prisma.session.deleteMany({
    where: {
      userId,

      tokenHash: {
        not: currentTokenHash,
      },
    },
  });
}

export async function deleteExpiredSessions(): Promise<void> {
  await prisma.session.deleteMany({
    where: {
      expiresAt: {
        lte: new Date(),
      },
    },
  });
}