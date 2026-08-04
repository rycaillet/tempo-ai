import { spawn } from "node:child_process";
import {
  copyFile,
  mkdir,
  readFile,
  rm,
} from "node:fs/promises";
import path from "node:path";

import type { Prisma } from "../generated/prisma/client.js";

import { env } from "../config/env.js";
import { analysisUploadDirectory } from "../config/upload.js";
import {
  completeAnalysis,
  failAnalysis,
  getAnalysisById,
} from "./analysis.service.js";

const ANALYSIS_TIMEOUT_MS = 15 * 60 * 1000;
const MAX_OUTPUT_LENGTH = 20 * 1024 * 1024;

const clubPhaseKeys = {
  address: "address",
  takeaway: "takeaway",
  topOfBackswing: "top",
  downswingStart: "downswing",
  impactReference: "impact",
  finishReference: "finish",
} as const;

type JsonRecord = Record<string, unknown>;

type ClubPhaseName = keyof typeof clubPhaseKeys;

type PipelineExecutionResult = {
  stdout: string;
  stderr: string;
};

export type ParsedPipelineResult = {
  analysis: Prisma.InputJsonObject;
  report: Prisma.InputJsonObject;
  artifacts: Prisma.InputJsonObject;
};

function isJsonRecord(
  value: unknown,
): value is JsonRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function isClubPhaseName(
  value: string,
): value is ClubPhaseName {
  return value in clubPhaseKeys;
}

function appendProcessOutput(
  existingOutput: string,
  chunk: Buffer,
  outputName: string,
): string {
  const nextOutput =
    existingOutput + chunk.toString("utf8");

  if (
    nextOutput.length >
    MAX_OUTPUT_LENGTH
  ) {
    throw new Error(
      `The analysis engine ${outputName} exceeded the maximum allowed size.`,
    );
  }

  return nextOutput;
}

function runAnalysisPipeline(
  videoPath: string,
): Promise<PipelineExecutionResult> {
  return new Promise((resolve, reject) => {
    const childProcess = spawn(
      env.PYTHON_EXECUTABLE,
      [
        "-m",
        "app.pipeline",
        videoPath,
      ],
      {
        cwd: env.ANALYSIS_ENGINE_PATH,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: "1",
        },
        stdio: [
          "ignore",
          "pipe",
          "pipe",
        ],
      },
    );

    let stdout = "";
    let stderr = "";
    let processSettled = false;

    const timeout = setTimeout(() => {
      if (processSettled) {
        return;
      }

      processSettled = true;
      childProcess.kill("SIGTERM");

      reject(
        new Error(
          `The analysis engine exceeded the ${
            ANALYSIS_TIMEOUT_MS / 60_000
          }-minute processing timeout.`,
        ),
      );
    }, ANALYSIS_TIMEOUT_MS);

    childProcess.stdout.on(
      "data",
      (chunk: Buffer) => {
        try {
          stdout = appendProcessOutput(
            stdout,
            chunk,
            "standard output",
          );
        } catch (error) {
          if (processSettled) {
            return;
          }

          processSettled = true;
          clearTimeout(timeout);
          childProcess.kill("SIGTERM");
          reject(error);
        }
      },
    );

    childProcess.stderr.on(
      "data",
      (chunk: Buffer) => {
        try {
          stderr = appendProcessOutput(
            stderr,
            chunk,
            "standard error",
          );
        } catch (error) {
          if (processSettled) {
            return;
          }

          processSettled = true;
          clearTimeout(timeout);
          childProcess.kill("SIGTERM");
          reject(error);
        }
      },
    );

    childProcess.on("error", (error) => {
      if (processSettled) {
        return;
      }

      processSettled = true;
      clearTimeout(timeout);

      reject(
        new Error(
          `Unable to start the analysis engine: ${error.message}`,
        ),
      );
    });

    childProcess.on(
      "close",
      (exitCode, signal) => {
        if (processSettled) {
          return;
        }

        processSettled = true;
        clearTimeout(timeout);

        if (exitCode !== 0) {
          const failureDetails =
            stderr.trim() ||
            stdout.trim() ||
            `Process exited with code ${String(
              exitCode,
            )}${
              signal
                ? ` after signal ${signal}`
                : ""
            }.`;

          reject(
            new Error(
              `The analysis engine failed: ${failureDetails}`,
            ),
          );

          return;
        }

        resolve({
          stdout,
          stderr,
        });
      },
    );
  });
}

function validateContractVersion({
  value,
  fieldName,
}: {
  value: unknown;
  fieldName: string;
}): void {
  if (
    value !==
    env.ANALYSIS_API_VERSION
  ) {
    throw new Error(
      `The analysis engine returned unsupported ${fieldName}. ` +
        `Expected ${env.ANALYSIS_API_VERSION}.`,
    );
  }
}

export function parsePipelineOutput(
  rawOutput: string,
): ParsedPipelineResult {
  const normalizedOutput =
    rawOutput.trim();

  if (
    normalizedOutput.length === 0
  ) {
    throw new Error(
      "The analysis engine completed without returning JSON output.",
    );
  }

  let parsedOutput: unknown;

  try {
    parsedOutput = JSON.parse(
      normalizedOutput,
    );
  } catch {
    throw new Error(
      "The analysis engine returned invalid JSON.",
    );
  }

  if (!isJsonRecord(parsedOutput)) {
    throw new Error(
      "The analysis engine returned an unexpected response format.",
    );
  }

  if (
    parsedOutput.success !== true
  ) {
    const pipelineError =
      typeof parsedOutput.error ===
      "string"
        ? parsedOutput.error
        : "The analysis engine reported an unsuccessful result.";

    throw new Error(pipelineError);
  }

  validateContractVersion({
    value: parsedOutput.apiVersion,
    fieldName: "API version",
  });

  const analysis =
    parsedOutput.analysis;

  if (!isJsonRecord(analysis)) {
    throw new Error(
      "The analysis engine response did not contain a valid analysis contract.",
    );
  }

  validateContractVersion({
    value: analysis.contractVersion,
    fieldName:
      "analysis contract version",
  });

  if (
    analysis.status !== "ready" &&
    analysis.status !== "partial"
  ) {
    throw new Error(
      "The analysis engine returned an unsupported analysis status.",
    );
  }

  const report =
    parsedOutput.report;

  if (!isJsonRecord(report)) {
    throw new Error(
      "The analysis engine response did not contain a valid detailed report.",
    );
  }

  const artifacts =
    parsedOutput.artifacts;

  if (!isJsonRecord(artifacts)) {
    throw new Error(
      "The analysis engine response did not contain valid artifact metadata.",
    );
  }

  return {
    analysis:
      analysis as Prisma.InputJsonObject,
    report:
      report as Prisma.InputJsonObject,
    artifacts:
      artifacts as Prisma.InputJsonObject,
  };
}

function buildClubArtifactDirectory(
  analysisId: string,
): string {
  return path.resolve(
    analysisUploadDirectory,
    analysisId,
    "club",
  );
}

function buildClubImageUrl(
  analysisId: string,
  filename: string,
): string {
  return [
    "/uploads/analyses",
    encodeURIComponent(analysisId),
    "club",
    encodeURIComponent(filename),
  ].join("/");
}

function getOptionalNumber(
  value: unknown,
): number | null {
  if (
    typeof value === "number" &&
    Number.isFinite(value)
  ) {
    return value;
  }

  return null;
}

function getOptionalString(
  value: unknown,
): string | null {
  if (
    typeof value === "string" &&
    value.trim().length > 0
  ) {
    return value.trim();
  }

  return null;
}

async function loadClubDetectionPayload(
  clubDetectionPath: string,
): Promise<JsonRecord> {
  const resolvedPath = path.resolve(
    clubDetectionPath,
  );

  const fileContents = await readFile(
    resolvedPath,
    "utf8",
  );

  let payload: unknown;

  try {
    payload = JSON.parse(
      fileContents,
    );
  } catch {
    throw new Error(
      "The club-detection artifact contained invalid JSON.",
    );
  }

  if (!isJsonRecord(payload)) {
    throw new Error(
      "The club-detection artifact did not contain a JSON object.",
    );
  }

  return payload;
}

async function copyClubPresentationArtifacts({
  analysisId,
  clubDetectionPath,
}: {
  analysisId: string;
  clubDetectionPath: string;
}): Promise<Prisma.InputJsonObject> {
  const clubDetection =
    await loadClubDetectionPayload(
      clubDetectionPath,
    );

  const frames =
    clubDetection.frames;

  if (!Array.isArray(frames)) {
    return {};
  }

  const destinationDirectory =
    buildClubArtifactDirectory(
      analysisId,
    );

  await rm(destinationDirectory, {
    recursive: true,
    force: true,
  });

  await mkdir(
    destinationDirectory,
    {
      recursive: true,
    },
  );

  const visualizations: JsonRecord =
    {};

  for (const frameValue of frames) {
    if (!isJsonRecord(frameValue)) {
      continue;
    }

    if (
      frameValue.isReferenceFrame !==
      true
    ) {
      continue;
    }

    const phase = getOptionalString(
      frameValue.phase,
    );

    const sourceImagePath =
      getOptionalString(
        frameValue.presentationImagePath,
      );

    if (
      phase === null ||
      !isClubPhaseName(phase) ||
      sourceImagePath === null
    ) {
      continue;
    }

    const phaseKey =
      clubPhaseKeys[phase];

    const filename =
      `${phaseKey}.jpg`;

    const resolvedSourcePath =
      path.resolve(
        sourceImagePath,
      );

    if (
      path
        .extname(resolvedSourcePath)
        .toLowerCase() !== ".jpg"
    ) {
      continue;
    }

    const destinationPath =
      path.resolve(
        destinationDirectory,
        filename,
      );

    await copyFile(
      resolvedSourcePath,
      destinationPath,
    );

    const visualization:
      JsonRecord = {
      phaseKey,
      sourcePhase: phase,
      imageUrl: buildClubImageUrl(
        analysisId,
        filename,
      ),
    };

    const frameIndex =
      getOptionalNumber(
        frameValue.frameIndex,
      );

    const timestampSeconds =
      getOptionalNumber(
        frameValue.timestampSeconds,
      );

    const confidence =
      getOptionalNumber(
        frameValue.confidence,
      );

    const geometrySource =
      getOptionalString(
        frameValue
          .presentationGeometrySource,
      );

    const detectionSource =
      getOptionalString(
        frameValue.detectionSource,
      );

    if (frameIndex !== null) {
      visualization.frameIndex =
        frameIndex;
    }

    if (
      timestampSeconds !== null
    ) {
      visualization.timestampSeconds =
        timestampSeconds;
    }

    if (confidence !== null) {
      visualization.confidence =
        confidence;
    }

    if (
      geometrySource !== null
    ) {
      visualization.geometrySource =
        geometrySource;
    }

    if (
      detectionSource !== null
    ) {
      visualization.detectionSource =
        detectionSource;
    }

    visualizations[phaseKey] =
      visualization;
  }

  if (
    Object.keys(
      visualizations,
    ).length === 0
  ) {
    await rm(destinationDirectory, {
      recursive: true,
      force: true,
    });
  }

  return visualizations as Prisma.InputJsonObject;
}

async function enrichAnalysisWithClubVisualizations({
  analysisId,
  analysis,
  artifacts,
}: {
  analysisId: string;
  analysis: Prisma.InputJsonObject;
  artifacts: Prisma.InputJsonObject;
}): Promise<Prisma.InputJsonObject> {
  const clubDetectionPath =
    getOptionalString(
      artifacts.clubDetectionPath,
    );

  if (
    clubDetectionPath === null
  ) {
    return analysis;
  }

  try {
    const clubVisualizations =
      await copyClubPresentationArtifacts({
        analysisId,
        clubDetectionPath,
      });

    if (
      Object.keys(
        clubVisualizations,
      ).length === 0
    ) {
      return analysis;
    }

    return {
      ...analysis,
      clubVisualizations,
    };
  } catch (error) {
    console.error(
      `Unable to publish club visualizations for ${analysisId}:`,
      error,
    );

    return analysis;
  }
}

async function processAnalysis(
  analysisId: string,
): Promise<void> {
  const analysisRecord =
    await getAnalysisById(
      analysisId,
    );

  if (!analysisRecord) {
    throw new Error(
      `Analysis ${analysisId} could not be found.`,
    );
  }

  if (
    !analysisRecord.storedFilename
  ) {
    throw new Error(
      `Analysis ${analysisId} does not have an uploaded video filename.`,
    );
  }

  const videoPath = path.resolve(
    analysisUploadDirectory,
    analysisRecord.storedFilename,
  );

  console.log(
    `Starting Python analysis pipeline for ${analysisId}.`,
  );

  const executionResult =
    await runAnalysisPipeline(
      videoPath,
    );

  if (
    executionResult.stderr
      .trim()
      .length > 0
  ) {
    console.log(
      `Analysis engine diagnostics for ${analysisId}:\n${executionResult.stderr.trim()}`,
    );
  }

  const pipelineResult =
    parsePipelineOutput(
      executionResult.stdout,
    );

  const enrichedAnalysis =
    await enrichAnalysisWithClubVisualizations({
      analysisId,
      analysis:
        pipelineResult.analysis,
      artifacts:
        pipelineResult.artifacts,
    });

  await completeAnalysis(
    analysisId,
    enrichedAnalysis,
    pipelineResult.report,
  );

  console.log(
    `Analysis ${analysisId} completed successfully.`,
  );
}

export function startAnalysisProcessing(
  analysisId: string,
): void {
  void processAnalysis(
    analysisId,
  ).catch(
    async (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "An unknown analysis-processing error occurred.";

      console.error(
        `Failed to process analysis ${analysisId}:`,
        error,
      );

      try {
        await failAnalysis(
          analysisId,
          message,
        );
      } catch (databaseError) {
        console.error(
          `Unable to mark analysis ${analysisId} as failed:`,
          databaseError,
        );
      }
    },
  );
}