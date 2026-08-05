import {
  hashPassword,
  verifyPassword,
} from "../auth/password.js";

import { createSession } from "../auth/session.js";
import { HttpError } from "../lib/http-error.js";
import { prisma } from "../lib/prisma.js";

export type PublicUser = {
  id: string;
  email: string;
  displayName: string;
  createdAt: Date;
  updatedAt: Date;
};

type RegisterUserInput = {
  email: string;
  displayName: string;
  password: string;
};

type LoginUserInput = {
  email: string;
  password: string;
};

function normalizeEmail(
  email: string,
): string {
  return email.trim().toLowerCase();
}

export async function registerUser(
  input: RegisterUserInput,
): Promise<{
  user: PublicUser;
  sessionToken: string;
}> {
  const email = normalizeEmail(
    input.email,
  );

  const displayName =
    input.displayName.trim();

  const existingUser =
    await prisma.user.findUnique({
      where: {
        email,
      },

      select: {
        id: true,
      },
    });

  if (existingUser) {
    throw new HttpError(
      409,
      "An account with that email already exists.",
    );
  }

  const passwordHash =
    await hashPassword(input.password);

  const user =
    await prisma.user.create({
      data: {
        email,
        displayName,
        passwordHash,
      },

      select: {
        id: true,
        email: true,
        displayName: true,
        createdAt: true,
        updatedAt: true,
      },
    });

  const session =
    await createSession(user.id);

  return {
    user,
    sessionToken: session.token,
  };
}

export async function loginUser(
  input: LoginUserInput,
): Promise<{
  user: PublicUser;
  sessionToken: string;
}> {
  const email = normalizeEmail(
    input.email,
  );

  const user =
    await prisma.user.findUnique({
      where: {
        email,
      },

      select: {
        id: true,
        email: true,
        displayName: true,
        passwordHash: true,
        createdAt: true,
        updatedAt: true,
      },
    });

  const passwordMatches =
    user !== null &&
    (await verifyPassword(
      user.passwordHash,
      input.password,
    ));

  if (!user || !passwordMatches) {
    throw new HttpError(
      401,
      "The email or password is incorrect.",
    );
  }

  const session =
    await createSession(user.id);

  return {
    user: {
      id: user.id,
      email: user.email,
      displayName: user.displayName,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
    },

    sessionToken: session.token,
  };
}