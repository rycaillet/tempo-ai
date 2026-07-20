import type {
  NextFunction,
  Request,
  Response,
} from "express";
import multer from "multer";

import { uploadAnalysisVideo } from "../config/upload.js";

export function handleAnalysisVideoUpload(
  request: Request,
  response: Response,
  next: NextFunction,
) {
  uploadAnalysisVideo.single("video")(
    request,
    response,
    (error: unknown) => {
      if (!error) {
        next();
        return;
      }

      if (error instanceof multer.MulterError) {
        if (error.code === "LIMIT_FILE_SIZE") {
          response.status(413).json({
            message:
              "The selected video must be smaller than 250 MB.",
          });

          return;
        }

        if (error.code === "LIMIT_UNEXPECTED_FILE") {
          response.status(400).json({
            message:
              'The uploaded video must use the form field name "video".',
          });

          return;
        }

        response.status(400).json({
          message: error.message,
        });

        return;
      }

      if (error instanceof Error) {
        response.status(400).json({
          message: error.message,
        });

        return;
      }

      response.status(400).json({
        message: "The video upload could not be processed.",
      });
    },
  );
}