import type { ErrorRequestHandler } from "express";
import multer from "multer";

import { env } from "../config/env.js";
import { HttpError } from "../lib/http-error.js";

export const errorHandler: ErrorRequestHandler = (
  error,
  _request,
  response,
  _next,
) => {
  if (error instanceof HttpError) {
    response.status(error.statusCode).json({
      message: error.message,

      ...(error.details !== undefined
        ? {
            details: error.details,
          }
        : {}),
    });

    return;
  }

  if (error instanceof multer.MulterError) {
    response.status(400).json({
      message:
        error.code === "LIMIT_FILE_SIZE"
          ? "The selected video is too large."
          : "The video upload could not be accepted.",
    });

    return;
  }

  console.error(error);

  response.status(500).json({
    message:
      "An unexpected server error occurred.",

    ...(env.NODE_ENV === "development" &&
    error instanceof Error
      ? {
          error: error.message,
        }
      : {}),
  });
};