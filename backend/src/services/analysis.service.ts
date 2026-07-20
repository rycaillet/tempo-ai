import { prisma } from "../lib/prisma.js";

type CreateAnalysisInput = {
  originalFilename: string;
  mimeType?: string;
  fileSizeBytes?: number;
};

export async function createAnalysis(input: CreateAnalysisInput) {
  return prisma.analysis.create({
    data: {
      originalFilename: input.originalFilename,
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