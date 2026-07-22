import { demoAnalysis } from "../data/analysis";
import type { SwingAnalysis } from "../types/analysis";

const apiBaseUrl =
  import.meta.env.VITE_API_URL ?? "http://localhost:5001/api";

const apiOrigin = apiBaseUrl.replace(/\/api\/?$/, "");

export type AnalysisStatus =
  | "UPLOADING"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED";

export type AnalysisRecord = {
  id: string;
  status: AnalysisStatus;
  originalFilename: string;
  storedFilename: string | null;
  mimeType: string | null;
  fileSizeBytes: number | null;
  failureReason: string | null;
  swingScore: number | null;
  tempoRatio: number | null;
  backswingSeconds: number | null;
  downswingSeconds: number | null;
  consistencyScore: number | null;
  primaryFinding: string | null;
  recommendation: string | null;
  createdAt: string;
  updatedAt: string;
};

type AnalysisResponse = {
  analysis: AnalysisRecord;
};

type AnalysesResponse = {
  analyses: AnalysisRecord[];
};

async function parseResponse<T extends object>(
  response: Response,
): Promise<T> {
  let data: T | { message?: string };

  try {
    data = (await response.json()) as T | {
      message?: string;
    };
  } catch {
    throw new Error(
      response.ok
        ? "TempoAI received an invalid server response."
        : "TempoAI could not complete the request.",
    );
  }

  if (!response.ok) {
    const message =
      "message" in data && typeof data.message === "string"
        ? data.message
        : "The analysis request failed.";

    throw new Error(message);
  }

  return data as T;
}

export async function createAnalysis(
  file: File,
): Promise<AnalysisRecord> {
  const formData = new FormData();

  formData.append("video", file);

  const response = await fetch(`${apiBaseUrl}/analyses`, {
    method: "POST",
    body: formData,
  });

  const data =
    await parseResponse<AnalysisResponse>(response);

  return data.analysis;
}

export async function getAnalysisRecord(
  analysisId: string,
): Promise<AnalysisRecord> {
  const response = await fetch(
    `${apiBaseUrl}/analyses/${encodeURIComponent(
      analysisId,
    )}`,
    {
      cache: "no-store",
    },
  );

  const data =
    await parseResponse<AnalysisResponse>(response);

  return data.analysis;
}

export async function getAnalysisRecords(): Promise<
  AnalysisRecord[]
> {
  const response = await fetch(`${apiBaseUrl}/analyses`, {
    cache: "no-store",
  });

  const data =
    await parseResponse<AnalysesResponse>(response);

  return data.analyses;
}

function formatAnalysisDate(dateValue: string) {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return demoAnalysis.summary.date;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function createAnalysisTitle(filename: string) {
  const withoutExtension = filename.replace(
    /\.[^/.]+$/,
    "",
  );

  const cleanedName = withoutExtension
    .replace(/[-_]+/g, " ")
    .trim();

  if (!cleanedName) {
    return demoAnalysis.summary.title;
  }

  return cleanedName.replace(/\b\w/g, (character) =>
    character.toUpperCase(),
  );
}

function createVideoUrl(
  storedFilename: string | null,
): string | null {
  if (!storedFilename) {
    return null;
  }

  return `${apiOrigin}/uploads/analyses/${encodeURIComponent(
    storedFilename,
  )}`;
}

function mapBackendAnalysis(
  record: AnalysisRecord,
): SwingAnalysis {
  const mappedMetrics = demoAnalysis.metrics.map(
    (metric) => {
      const searchableName =
        `${metric.id} ${metric.label}`.toLowerCase();

      if (
        searchableName.includes("consistency") &&
        record.consistencyScore !== null
      ) {
        return {
          ...metric,
          score: record.consistencyScore,
        };
      }

      if (
        searchableName.includes("tempo") &&
        record.tempoRatio !== null
      ) {
        const tempoDifference = Math.abs(
          3 - record.tempoRatio,
        );

        const tempoScore = Math.max(
          0,
          Math.min(
            100,
            Math.round(
              100 - tempoDifference * 35,
            ),
          ),
        );

        return {
          ...metric,
          score: tempoScore,
          description: `${record.tempoRatio.toFixed(
            2,
          )}:1 backswing-to-downswing tempo ratio.`,
        };
      }

      return metric;
    },
  );

  const mappedFindings = demoAnalysis.findings.map(
    (finding, index) => {
      if (index !== 0) {
        return finding;
      }

      return {
        ...finding,
        title:
          record.primaryFinding ?? finding.title,
        explanation:
          record.recommendation ??
          finding.explanation,
      };
    },
  );

  const coachingSummary = [
    record.primaryFinding,
    record.recommendation,
  ]
    .filter(
      (value): value is string => Boolean(value),
    )
    .join(" ");

  return {
    ...demoAnalysis,
    videoUrl: createVideoUrl(record.storedFilename),
    videoMimeType: record.mimeType,
    summary: {
      ...demoAnalysis.summary,
      id: record.id,
      title: createAnalysisTitle(
        record.originalFilename,
      ),
      date: formatAnalysisDate(record.createdAt),
      overallScore:
        record.swingScore ??
        demoAnalysis.summary.overallScore,
      summary:
        coachingSummary ||
        demoAnalysis.summary.summary,
      strength:
        record.consistencyScore !== null
          ? `Your swing consistency scored ${record.consistencyScore} out of 100.`
          : demoAnalysis.summary.strength,
    },
    metrics: mappedMetrics,
    findings: mappedFindings,
  };
}

export async function getAnalysis(
  analysisId: string,
): Promise<SwingAnalysis> {
  const record =
    await getAnalysisRecord(analysisId);

  if (record.status === "FAILED") {
    throw new Error(
      record.failureReason ??
        "The swing analysis failed.",
    );
  }

  if (record.status !== "COMPLETED") {
    throw new Error(
      "The swing analysis is not complete yet.",
    );
  }

  return mapBackendAnalysis(record);
}