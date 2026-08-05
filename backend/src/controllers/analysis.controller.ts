import { unlink } from "node:fs/promises";

import type {
  NextFunction,
  Request,
  Response,
} from "express";

import type { AuthenticatedLocals } from "../middleware/require-auth.middleware.js";
import { startAnalysisProcessing } from "../services/analysis-processing.service.js";
import {
  createAnalysis,
  deleteAnalysisForUser,
  getAnalysesForUser,
  getAnalysisByIdForUser,
} from "../services/analysis.service.js";

async function removeUploadedFile(
  filePath: string,
) {
  try {
    await unlink(filePath);
  } catch (error) {
    console.error(
      `Unable to remove uploaded file at ${filePath}:`,
      error,
    );
  }
}

function getAnalysisId(
  request: Request,
): string | null {
  const analysisId =
    request.params.id;

  if (
    typeof analysisId !== "string" ||
    analysisId.trim().length === 0
  ) {
    return null;
  }

  return analysisId.trim();
}

export async function createAnalysisHandler(
  request: Request,
  response: Response<
    unknown,
    AuthenticatedLocals
  >,
  next: NextFunction,
) {
  const uploadedFile = request.file;

  if (!uploadedFile) {
    response.status(400).json({
      message:
        "Select a golf swing video to upload.",
    });

    return;
  }

  try {
    const analysis = await createAnalysis({
      userId:
        response.locals.authUser.id,
      originalFilename:
        uploadedFile.originalname,
      storedFilename:
        uploadedFile.filename,
      mimeType:
        uploadedFile.mimetype,
      fileSizeBytes:
        uploadedFile.size,
    });

    startAnalysisProcessing(
      analysis.id,
    );

    response.status(201).json({
      analysis,
    });
  } catch (error) {
    await removeUploadedFile(
      uploadedFile.path,
    );

    next(error);
  }
}

export async function getAnalysisHandler(
  request: Request,
  response: Response<
    unknown,
    AuthenticatedLocals
  >,
  next: NextFunction,
) {
  try {
    const analysisId =
      getAnalysisId(request);

    if (!analysisId) {
      response.status(400).json({
        message:
          "A valid analysis ID is required.",
      });

      return;
    }

    const analysis =
      await getAnalysisByIdForUser(
        analysisId,
        response.locals.authUser.id,
      );

    if (!analysis) {
      response.status(404).json({
        message:
          "Analysis not found.",
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
  response: Response<
    unknown,
    AuthenticatedLocals
  >,
  next: NextFunction,
) {
  try {
    const analyses =
      await getAnalysesForUser(
        response.locals.authUser.id,
      );

    response.status(200).json({
      analyses,
    });
  } catch (error) {
    next(error);
  }
}

export async function deleteAnalysisHandler(
  request: Request,
  response: Response<
    unknown,
    AuthenticatedLocals
  >,
  next: NextFunction,
) {
  try {
    const analysisId =
      getAnalysisId(request);

    if (!analysisId) {
      response.status(400).json({
        message:
          "A valid analysis ID is required.",
      });

      return;
    }

    const result =
      await deleteAnalysisForUser(
        analysisId,
        response.locals.authUser.id,
      );

    if (result.status === "not_found") {
      response.status(404).json({
        message:
          "Analysis not found.",
      });

      return;
    }

    if (result.status === "processing") {
      response.status(409).json({
        message:
          "This analysis is still processing and cannot be deleted yet.",
      });

      return;
    }

    response.status(200).json({
      message:
        "The swing analysis was deleted.",
    });
  } catch (error) {
    next(error);
  }
}