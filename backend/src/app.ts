import cors from "cors";
import express from "express";
import helmet from "helmet";

import { env } from "./config/env.js";
import { errorHandler } from "./middleware/errorHandler.js";
import healthRouter from "./routes/health.routes.js";
import analysisRouter from "./routes/analysis.routes.js";

const app = express();

app.use(helmet());

app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
  }),
);

app.use(express.json());

app.use((req, res, next) => {
  const startedAt = Date.now();

  res.on("finish", () => {
    const duration = Date.now() - startedAt;

    console.log(
      `${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`,
    );
  });

  next();
});

app.get("/", (_request, response) => {
  response.status(200).json({
    message: "TempoAI API",
  });
});

app.use("/api/health", healthRouter);
app.use("/api/analyses", analysisRouter);

app.use(errorHandler);

export default app;