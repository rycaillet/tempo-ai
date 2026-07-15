import cors from "cors";
import express from "express";
import helmet from "helmet";

import { env } from "./config/env.js";
import { errorHandler } from "./middleware/errorHandler.js";
import healthRouter from "./routes/health.routes.js";

const app = express();

app.use(helmet());

app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
  }),
);

app.use(express.json());

app.get("/", (_request, response) => {
  response.status(200).json({
    message: "TempoAI API",
  });
});

app.use("/api/health", healthRouter);

app.use(errorHandler);

export default app;