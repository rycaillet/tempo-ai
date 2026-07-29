import path from "node:path";

import "dotenv/config";
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z
    .enum(["development", "test", "production"])
    .default("development"),

  PORT: z.coerce.number().int().positive().default(5001),

  CLIENT_URL: z.string().url().default("http://localhost:5173"),

  ANALYSIS_ENGINE_PATH: z
    .string()
    .min(1)
    .default("../analysis-engine"),

  PYTHON_EXECUTABLE: z
    .string()
    .min(1)
    .default("../analysis-engine/.venv/bin/python"),
});

const result = envSchema.safeParse(process.env);

if (!result.success) {
  console.error(
    "Invalid environment configuration:",
    result.error.flatten().fieldErrors,
  );

  throw new Error("Environment validation failed.");
}

export const env = {
  ...result.data,

  ANALYSIS_ENGINE_PATH: path.resolve(
    process.cwd(),
    result.data.ANALYSIS_ENGINE_PATH,
  ),

  PYTHON_EXECUTABLE: path.resolve(
    process.cwd(),
    result.data.PYTHON_EXECUTABLE,
  ),
};