import { randomUUID } from "node:crypto";
import { mkdirSync } from "node:fs";
import path from "node:path";

import multer from "multer";

const maximumFileSize = 250 * 1024 * 1024;

const allowedMimeTypes = new Set([
  "video/mp4",
  "video/quicktime",
  "video/x-quicktime",
  "video/webm",
  "application/octet-stream",
]);

const allowedExtensions = new Set([".mp4", ".mov", ".webm"]);

export const analysisUploadDirectory = path.resolve(
  process.cwd(),
  "uploads",
  "analyses",
);

mkdirSync(analysisUploadDirectory, {
  recursive: true,
});

const storage = multer.diskStorage({
  destination: (_request, _file, callback) => {
    callback(null, analysisUploadDirectory);
  },

  filename: (_request, file, callback) => {
    const extension = path.extname(file.originalname).toLowerCase();
    const safeExtension = allowedExtensions.has(extension)
      ? extension
      : "";

    callback(null, `${randomUUID()}${safeExtension}`);
  },
});

export const uploadAnalysisVideo = multer({
  storage,

  limits: {
    fileSize: maximumFileSize,
    files: 1,
  },

  fileFilter: (_request, file, callback) => {
    const extension = path.extname(file.originalname).toLowerCase();

    const hasAllowedMimeType = allowedMimeTypes.has(file.mimetype);
    const hasAllowedExtension = allowedExtensions.has(extension);

    if (!hasAllowedMimeType || !hasAllowedExtension) {
      callback(
        new Error(
          "Choose an MP4, MOV, or WEBM video.",
        ),
      );

      return;
    }

    callback(null, true);
  },
});