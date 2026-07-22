import { prisma } from "../lib/prisma.js";
import { generateAnalysisResult } from "./analysis-generator.service.js";

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
  const generatedAnalysis = generateAnalysisResult();

  return prisma.analysis.update({
    where: {
      id,
    },
    data: {
      status: "COMPLETED",

      swingScore: generatedAnalysis.swingScore,
      tempoRatio: generatedAnalysis.tempoRatio,
      backswingSeconds:
        generatedAnalysis.backswingSeconds,
      downswingSeconds:
        generatedAnalysis.downswingSeconds,
      consistencyScore:
        generatedAnalysis.consistencyScore,
      primaryFinding:
        generatedAnalysis.primaryFinding,
      recommendation:
        generatedAnalysis.recommendation,
      phaseTimings:
        generatedAnalysis.phaseTimings,
    },
  });
}