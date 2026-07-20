import { prisma } from "../lib/prisma.js";

type CreateAnalysisInput = {
  originalFilename: string;
  storedFilename: string;
  mimeType: string;
  fileSizeBytes: number;
};

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

export async function completeAnalysis(id: string) {
  return prisma.analysis.update({
    where: {
      id,
    },
    data: {
      status: "COMPLETED",
      swingScore: 87,
      tempoRatio: 2.92,
      backswingSeconds: 0.73,
      downswingSeconds: 0.25,
      consistencyScore: 82,
      primaryFinding:
        "Early hip rotation during the downswing",
      recommendation:
        "Keep your chest closed slightly longer while starting the downswing from the lower body.",
    },
  });
}