import { unlink } from "node:fs/promises";

import type {
  NextFunction,
  Request,
  Response,
} from "express";

import { startAnalysisProcessing } from "../services/analysis-processing.service.js";
import {
  createAnalysis,
  getAnalyses,
  getAnalysisById,
} from "../services/analysis.service.js";

async function removeUploadedFile(filePath: string) {
  try {
    await unlink(filePath);
  } catch (error) {
    console.error(
      `Unable to remove uploaded file at ${filePath}:`,
      error,
    );
  }
}

export async function createAnalysisHandler(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  const uploadedFile = request.file;

  if (!uploadedFile) {
    response.status(400).json({
      message: "Select a golf swing video to upload.",
    });

    return;
  }

  try {
    const analysis = await createAnalysis({
      originalFilename: uploadedFile.originalname,
      storedFilename: uploadedFile.filename,
      mimeType: uploadedFile.mimetype,
      fileSizeBytes: uploadedFile.size,
    });

    startAnalysisProcessing(analysis.id);

    response.status(201).json({
      analysis,
    });
  } catch (error) {
    await removeUploadedFile(uploadedFile.path);
    next(error);
  }
}

export async function getAnalysisHandler(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  try {
    const analysisId = request.params.id;

    if (
      typeof analysisId !== "string" ||
      analysisId.trim().length === 0
    ) {
      response.status(400).json({
        message: "A valid analysis ID is required.",
      });

      return;
    }

    const analysis = await getAnalysisById(analysisId);

    if (!analysis) {
      response.status(404).json({
        message: "Analysis not found.",
      });

      return;
    }

    response.status(200).json({
      analysis,
    });
  } catch (error) {
    next(error);
  }
}

export async function getAnalysesHandler(
  _request: Request,
  response: Response,
  next: NextFunction,
) {
  try {
    const analyses = await getAnalyses();

    response.status(200).json({
      analyses,
    });
  } catch (error) {
    next(error);
  }
}