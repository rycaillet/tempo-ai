import { rm } from "node:fs/promises";
import path from "node:path";

import type { Prisma } from "../generated/prisma/client.js";

import { analysisUploadDirectory } from "../config/upload.js";
import { prisma } from "../lib/prisma.js";

const ANALYSIS_STALE_AFTER_MS =
  16 * 60 * 1000;

const STALE_ANALYSIS_FAILURE_REASON =
  "This analysis was interrupted before processing completed. Please upload the swing again.";

type CreateAnalysisInput = {
  userId: string;
  originalFilename: string;
  storedFilename: string;
  mimeType: string;
  fileSizeBytes: number;
};

type JsonRecord = Record<string, unknown>;

export type DeleteAnalysisResult =
  | {
      status: "deleted";
    }
  | {
      status: "not_found";
    }
  | {
      status: "processing";
    };

function isJsonRecord(value: unknown): value is JsonRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function getNestedValue(
  source: unknown,
  path: readonly string[],
): unknown {
  let currentValue: unknown = source;

  for (const key of path) {
    if (Array.isArray(currentValue)) {
      const index = Number.parseInt(key, 10);

      if (
        !Number.isInteger(index) ||
        index < 0 ||
        index >= currentValue.length
      ) {
        return undefined;
      }

      currentValue = currentValue[index];
      continue;
    }

    if (!isJsonRecord(currentValue)) {
      return undefined;
    }

    currentValue = currentValue[key];
  }

  return currentValue;
}

function getFirstNumber(
  source: unknown,
  candidatePaths: readonly (readonly string[])[],
): number | undefined {
  for (const candidatePath of candidatePaths) {
    const value = getNestedValue(
      source,
      candidatePath,
    );

    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return value;
    }
  }

  return undefined;
}

function getFirstString(
  source: unknown,
  candidatePaths: readonly (readonly string[])[],
): string | undefined {
  for (const candidatePath of candidatePaths) {
    const value = getNestedValue(
      source,
      candidatePath,
    );

    if (
      typeof value === "string" &&
      value.trim().length > 0
    ) {
      return value.trim();
    }
  }

  return undefined;
}

function getFirstJsonRecord(
  source: unknown,
  candidatePaths: readonly (readonly string[])[],
): Prisma.InputJsonObject | undefined {
  for (const candidatePath of candidatePaths) {
    const value = getNestedValue(
      source,
      candidatePath,
    );

    if (isJsonRecord(value)) {
      return value as Prisma.InputJsonObject;
    }
  }

  return undefined;
}

function extractFirstMessage(
  value: unknown,
): string | undefined {
  if (
    typeof value === "string" &&
    value.trim().length > 0
  ) {
    return value.trim();
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const message =
        extractFirstMessage(item);

      if (message) {
        return message;
      }
    }

    return undefined;
  }

  if (!isJsonRecord(value)) {
    return undefined;
  }

  const preferredKeys = [
    "message",
    "summary",
    "description",
    "finding",
    "recommendation",
    "title",
    "primaryFocus",
    "overallFinding",
  ] as const;

  for (const key of preferredKeys) {
    const message =
      extractFirstMessage(value[key]);

    if (message) {
      return message;
    }
  }

  return undefined;
}

function getStaleAnalysisCutoff() {
  return new Date(
    Date.now() -
      ANALYSIS_STALE_AFTER_MS,
  );
}

function getStoredVideoPath(
  storedFilename: string,
): string {
  const safeFilename =
    path.basename(storedFilename);

  return path.resolve(
    analysisUploadDirectory,
    safeFilename,
  );
}

function getAnalysisArtifactDirectory(
  analysisId: string,
): string {
  const safeAnalysisId =
    path.basename(analysisId);

  return path.resolve(
    analysisUploadDirectory,
    safeAnalysisId,
  );
}

async function removeAnalysisFiles({
  analysisId,
  storedFilename,
}: {
  analysisId: string;
  storedFilename: string | null;
}): Promise<void> {
  const removalOperations: Promise<void>[] = [];

  if (storedFilename) {
    removalOperations.push(
      rm(
        getStoredVideoPath(
          storedFilename,
        ),
        {
          force: true,
        },
      ),
    );
  }

  removalOperations.push(
    rm(
      getAnalysisArtifactDirectory(
        analysisId,
      ),
      {
        recursive: true,
        force: true,
      },
    ),
  );

  await Promise.all(removalOperations);
}

async function failStaleAnalysisById(
  id: string,
): Promise<void> {
  await prisma.analysis.updateMany({
    where: {
      id,
      status: "PROCESSING",

      updatedAt: {
        lte: getStaleAnalysisCutoff(),
      },
    },

    data: {
      status: "FAILED",
      failureReason:
        STALE_ANALYSIS_FAILURE_REASON,
    },
  });
}

async function failAllStaleAnalyses(): Promise<void> {
  await prisma.analysis.updateMany({
    where: {
      status: "PROCESSING",

      updatedAt: {
        lte: getStaleAnalysisCutoff(),
      },
    },

    data: {
      status: "FAILED",
      failureReason:
        STALE_ANALYSIS_FAILURE_REASON,
    },
  });
}

export async function createAnalysis(
  input: CreateAnalysisInput,
) {
  return prisma.analysis.create({
    data: {
      userId: input.userId,
      originalFilename:
        input.originalFilename,
      storedFilename:
        input.storedFilename,
      mimeType: input.mimeType,
      fileSizeBytes:
        input.fileSizeBytes,
      status: "PROCESSING",
    },
  });
}

export async function getAnalysisById(
  id: string,
) {
  await failStaleAnalysisById(id);

  return prisma.analysis.findUnique({
    where: {
      id,
    },
  });
}

export async function getAnalysisByIdForUser(
  id: string,
  userId: string,
) {
  await failStaleAnalysisById(id);

  return prisma.analysis.findFirst({
    where: {
      id,
      userId,
    },
  });
}

export async function getAnalysesForUser(
  userId: string,
) {
  await failAllStaleAnalyses();

  return prisma.analysis.findMany({
    where: {
      userId,
    },

    orderBy: {
      createdAt: "desc",
    },
  });
}

export async function deleteAnalysisForUser(
  id: string,
  userId: string,
): Promise<DeleteAnalysisResult> {
  await failStaleAnalysisById(id);

  const analysis =
    await prisma.analysis.findFirst({
      where: {
        id,
        userId,
      },

      select: {
        id: true,
        status: true,
        storedFilename: true,
      },
    });

  if (!analysis) {
    return {
      status: "not_found",
    };
  }

  if (
    analysis.status === "PROCESSING" ||
    analysis.status === "UPLOADING"
  ) {
    return {
      status: "processing",
    };
  }

  await removeAnalysisFiles({
    analysisId: analysis.id,
    storedFilename:
      analysis.storedFilename,
  });

  const deletionResult =
    await prisma.analysis.deleteMany({
      where: {
        id,
        userId,
      },
    });

  if (deletionResult.count === 0) {
    return {
      status: "not_found",
    };
  }

  return {
    status: "deleted",
  };
}

export async function completeAnalysis(
  id: string,
  analysisPayload: Prisma.InputJsonValue,
  detailedReport: Prisma.InputJsonValue,
) {
  const swingScore = getFirstNumber(
    analysisPayload,
    [
      ["score", "overallScore"],
    ],
  );

  const tempoRatio = getFirstNumber(
    detailedReport,
    [
      [
        "metrics",
        "tempo",
        "backswingToDownswingRatio",
      ],
      ["summary", "tempoRatio"],
      ["metrics", "tempo", "ratio"],
      [
        "metrics",
        "tempo",
        "tempoRatio",
      ],
    ],
  );

  const backswingSeconds = getFirstNumber(
    detailedReport,
    [
      [
        "metrics",
        "tempo",
        "backswingDurationSeconds",
      ],
      [
        "metrics",
        "tempo",
        "measurements",
        "backswingDurationSeconds",
      ],
      [
        "metrics",
        "tempo",
        "backswingSeconds",
      ],
    ],
  );

  const downswingSeconds = getFirstNumber(
    detailedReport,
    [
      [
        "metrics",
        "tempo",
        "downswingDurationSeconds",
      ],
      [
        "metrics",
        "tempo",
        "measurements",
        "downswingDurationSeconds",
      ],
      [
        "metrics",
        "tempo",
        "downswingSeconds",
      ],
    ],
  );

  const consistencyScore =
    getFirstNumber(
      detailedReport,
      [
        [
          "scoring",
          "consistencyScore",
        ],
        [
          "summary",
          "consistencyScore",
        ],
      ],
    );

  const primaryFinding =
    getFirstString(
      analysisPayload,
      [
        [
          "findings",
          "overallFinding",
        ],
        [
          "coaching",
          "headline",
        ],
        [
          "coaching",
          "overview",
        ],
      ],
    ) ??
    extractFirstMessage(
      getNestedValue(
        analysisPayload,
        ["findings"],
      ),
    );

  const recommendation =
    getFirstString(
      analysisPayload,
      [
        [
          "coaching",
          "primaryFocus",
        ],
        [
          "recommendations",
          "items",
          "0",
          "summary",
        ],
        [
          "recommendations",
          "items",
          "0",
          "title",
        ],
      ],
    ) ??
    extractFirstMessage(
      getNestedValue(
        analysisPayload,
        ["recommendations"],
      ),
    );

  const phaseTimings =
    getFirstJsonRecord(
      detailedReport,
      [
        ["phaseFrames"],
      ],
    );

  return prisma.analysis.update({
    where: {
      id,
    },

    data: {
      status: "COMPLETED",
      failureReason: null,
      analysisPayload,
      analysisReport: detailedReport,

      ...(swingScore !== undefined
        ? {
            swingScore:
              Math.round(swingScore),
          }
        : {}),

      ...(tempoRatio !== undefined
        ? {
            tempoRatio,
          }
        : {}),

      ...(backswingSeconds !== undefined
        ? {
            backswingSeconds,
          }
        : {}),

      ...(downswingSeconds !== undefined
        ? {
            downswingSeconds,
          }
        : {}),

      ...(consistencyScore !== undefined
        ? {
            consistencyScore:
              Math.round(
                consistencyScore,
              ),
          }
        : {}),

      ...(primaryFinding
        ? {
            primaryFinding,
          }
        : {}),

      ...(recommendation
        ? {
            recommendation,
          }
        : {}),

      ...(phaseTimings
        ? {
            phaseTimings,
          }
        : {}),
    },
  });
}

export async function failAnalysis(
  id: string,
  reason: string,
) {
  const normalizedReason =
    reason.trim().length > 0
      ? reason
          .trim()
          .slice(0, 1000)
      : "The analysis engine failed without providing an error message.";

  return prisma.analysis.update({
    where: {
      id,
    },

    data: {
      status: "FAILED",
      failureReason:
        normalizedReason,
    },
  });
}