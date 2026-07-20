import type { NextFunction, Request, Response } from "express";
import { z } from "zod";

import {
  createAnalysis,
  getAnalyses,
  getAnalysisById,
} from "../services/analysis.service.js";

const createAnalysisSchema = z.object({
  originalFilename: z.string().trim().min(1),
  mimeType: z.string().trim().optional(),
  fileSizeBytes: z.number().int().nonnegative().optional(),
});

export async function createAnalysisHandler(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  try {
    const input = createAnalysisSchema.parse(request.body);
    const analysis = await createAnalysis(input);

    response.status(201).json({
      analysis,
    });
  } catch (error) {
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

    if (typeof analysisId !== "string" || analysisId.trim().length === 0) {
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