import type { Prisma } from "../generated/prisma/client.js";

import { prisma } from "../lib/prisma.js";

type CreateAnalysisInput = {
  originalFilename: string;
  storedFilename: string;
  mimeType: string;
  fileSizeBytes: number;
};

type JsonRecord = Record<string, unknown>;

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
    const value = getNestedValue(source, candidatePath);

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
    const value = getNestedValue(source, candidatePath);

    if (
      typeof value === "string" &&
      value.trim().length > 0
    ) {
      return value.trim();
    }
  }

  return undefined;
}

function extractFirstMessage(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim().length > 0) {
    return value.trim();
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const message = extractFirstMessage(item);

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
  ] as const;

  for (const key of preferredKeys) {
    const message = extractFirstMessage(value[key]);

    if (message) {
      return message;
    }
  }

  return undefined;
}

export async function createAnalysis(
  input: CreateAnalysisInput,
) {
  return prisma.analysis.create({
    data: {
      originalFilename: input.originalFilename,
      storedFilename: input.storedFilename,
      mimeType: input.mimeType,
      fileSizeBytes: input.fileSizeBytes,
      status: "PROCESSING",
    },
  });
}

export async function getAnalysisById(id: string) {
  return prisma.analysis.findUnique({
    where: {
      id,
    },
  });
}

export async function getAnalyses() {
  return prisma.analysis.findMany({
    orderBy: {
      createdAt: "desc",
    },
  });
}

export async function completeAnalysis(
  id: string,
  report: Prisma.InputJsonValue,
) {
  const swingScore = getFirstNumber(report, [
    ["scoring", "overallScore"],
  ]);

  const tempoRatio = getFirstNumber(report, [
    ["summary", "tempoRatio"],
    ["metrics", "tempo", "ratio"],
    ["metrics", "tempo", "tempoRatio"],
  ]);

  const backswingSeconds = getFirstNumber(report, [
    [
      "metrics",
      "tempo",
      "measurements",
      "backswingDurationSeconds",
    ],
    ["metrics", "tempo", "backswingSeconds"],
  ]);

  const downswingSeconds = getFirstNumber(report, [
    [
      "metrics",
      "tempo",
      "measurements",
      "downswingDurationSeconds",
    ],
    ["metrics", "tempo", "downswingSeconds"],
  ]);

  const consistencyScore = getFirstNumber(report, [
    ["scoring", "consistencyScore"],
    ["summary", "consistencyScore"],
  ]);

  const primaryFinding =
    getFirstString(report, [
      ["summary", "primaryFinding"],
      ["coaching", "primaryFinding"],
    ]) ??
    extractFirstMessage(
      getNestedValue(report, ["findings"]),
    );

  const recommendation =
    getFirstString(report, [
      ["summary", "recommendation"],
      ["coaching", "recommendation"],
    ]) ??
    extractFirstMessage(
      getNestedValue(report, ["recommendations"]),
    );

  return prisma.analysis.update({
    where: {
      id,
    },
    data: {
      status: "COMPLETED",
      failureReason: null,
      analysisReport: report,

      ...(swingScore !== undefined
        ? {
            swingScore: Math.round(swingScore),
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
            consistencyScore: Math.round(consistencyScore),
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
    },
  });
}

export async function failAnalysis(
  id: string,
  reason: string,
) {
  const normalizedReason =
    reason.trim().length > 0
      ? reason.trim().slice(0, 1000)
      : "The analysis engine failed without providing an error message.";

  return prisma.analysis.update({
    where: {
      id,
    },
    data: {
      status: "FAILED",
      failureReason: normalizedReason,
    },
  });
}