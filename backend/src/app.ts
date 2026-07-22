import path from "node:path";
import { fileURLToPath } from "node:url";

import cors from "cors";
import express from "express";
import helmet from "helmet";

import { env } from "./config/env.js";
import { errorHandler } from "./middleware/errorHandler.js";
import analysisRouter from "./routes/analysis.routes.js";
import healthRouter from "./routes/health.routes.js";

const currentFilename = fileURLToPath(import.meta.url);
const currentDirectory = path.dirname(currentFilename);

const analysisUploadsDirectory = path.resolve(
  currentDirectory,
  "../uploads/analyses",
);

const app = express();

app.use(
  helmet({
    crossOriginResourcePolicy: {
      policy: "cross-origin",
    },
  }),
);

app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
  }),
);

app.use(express.json());

app.use((request, response, next) => {
  const startedAt = Date.now();

  response.on("finish", () => {
    const duration = Date.now() - startedAt;

    console.log(
      `${request.method} ${request.originalUrl} ${response.statusCode} ${duration}ms`,
    );
  });

  next();
});

app.get("/", (_request, response) => {
  response.status(200).json({
    message: "TempoAI API",
  });
});

app.use(
  "/uploads/analyses",
  express.static(analysisUploadsDirectory, {
    fallthrough: false,
    maxAge: env.NODE_ENV === "production" ? "1d" : 0,
  }),
);

app.use("/api/health", healthRouter);
app.use("/api/analyses", analysisRouter);

app.use(errorHandler);

export default app;