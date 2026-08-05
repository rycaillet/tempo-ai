import {
  hashPassword,
  verifyPassword,
} from "../auth/password.js";
import {
  createSession,
  revokeOtherSessions,
} from "../auth/session.js";
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

type UpdateProfileInput = {
  userId: string;
  displayName: string;
};

type ChangePasswordInput = {
  userId: string;
  currentPassword: string;
  newPassword: string;
  currentSessionToken: string;
};

const publicUserSelection = {
  id: true,
  email: true,
  displayName: true,
  createdAt: true,
  updatedAt: true,
} as const;

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

      select: publicUserSelection,
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
        ...publicUserSelection,
        passwordHash: true,
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

export async function updateUserProfile(
  input: UpdateProfileInput,
): Promise<PublicUser> {
  const displayName =
    input.displayName.trim();

  const existingUser =
    await prisma.user.findUnique({
      where: {
        id: input.userId,
      },

      select: {
        id: true,
      },
    });

  if (!existingUser) {
    throw new HttpError(
      404,
      "Account not found.",
    );
  }

  return prisma.user.update({
    where: {
      id: input.userId,
    },

    data: {
      displayName,
    },

    select: publicUserSelection,
  });
}

export async function changeUserPassword(
  input: ChangePasswordInput,
): Promise<void> {
  if (
    input.currentPassword ===
    input.newPassword
  ) {
    throw new HttpError(
      400,
      "Your new password must be different from your current password.",
    );
  }

  const user =
    await prisma.user.findUnique({
      where: {
        id: input.userId,
      },

      select: {
        id: true,
        passwordHash: true,
      },
    });

  if (!user) {
    throw new HttpError(
      404,
      "Account not found.",
    );
  }

  const currentPasswordMatches =
    await verifyPassword(
      user.passwordHash,
      input.currentPassword,
    );

  if (!currentPasswordMatches) {
    throw new HttpError(
      401,
      "Your current password is incorrect.",
    );
  }

  const newPasswordHash =
    await hashPassword(
      input.newPassword,
    );

  await prisma.user.update({
    where: {
      id: input.userId,
    },

    data: {
      passwordHash:
        newPasswordHash,
    },
  });

  await revokeOtherSessions(
    input.userId,
    input.currentSessionToken,
  );
}