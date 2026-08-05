import { mapBackendAnalysis } from "../mappers/analysisMapper";
import type { SwingAnalysis } from "../types/analysis";
import type {
  BackendAnalysisPayload,
  BackendAnalysisReport,
  BackendPhaseFrames,
  LegacyPhaseTimings,
} from "../types/backendAnalysis";

const apiBaseUrl =
  import.meta.env.VITE_API_URL ??
  "http://localhost:5001/api";

const apiOrigin = apiBaseUrl.replace(
  /\/api\/?$/,
  "",
);

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
  phaseTimings:
    | BackendPhaseFrames
    | LegacyPhaseTimings
    | null;
  analysisPayload: BackendAnalysisPayload | null;
  analysisReport: BackendAnalysisReport | null;
  createdAt: string;
  updatedAt: string;
};

export type AnalysisPreview =
  | {
      kind: "image";
      url: string;
    }
  | {
      kind: "video";
      url: string;
    };

type AnalysisResponse = {
  analysis: AnalysisRecord;
};

type AnalysesResponse = {
  analyses: AnalysisRecord[];
};

type MessageResponse = {
  message: string;
};

function createPublicAssetUrl(
  assetPath: string | undefined,
): string | null {
  if (!assetPath?.trim()) {
    return null;
  }

  const normalizedPath =
    assetPath.trim();

  if (
    /^https?:\/\//i.test(
      normalizedPath,
    )
  ) {
    return normalizedPath;
  }

  return `${apiOrigin}${
    normalizedPath.startsWith("/")
      ? ""
      : "/"
  }${normalizedPath}`;
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

export function getAnalysisPreview(
  analysis: AnalysisRecord,
): AnalysisPreview | null {
  /*
   * Prefer the original video because browsers apply
   * the phone recording's orientation metadata.
   *
   * Extracted visualization images can appear sideways
   * when that metadata is not carried into the image.
   */
  const videoUrl = createVideoUrl(
    analysis.storedFilename,
  );

  if (videoUrl) {
    return {
      kind: "video",
      url: videoUrl,
    };
  }

  const visualizations =
    analysis.analysisPayload
      ?.clubVisualizations;

  const previewImagePath =
    visualizations?.address?.imageUrl ??
    visualizations?.takeaway?.imageUrl ??
    visualizations?.top?.imageUrl ??
    visualizations?.downswing?.imageUrl ??
    visualizations?.impact?.imageUrl ??
    visualizations?.finish?.imageUrl;

  const previewImageUrl =
    createPublicAssetUrl(
      previewImagePath,
    );

  if (previewImageUrl) {
    return {
      kind: "image",
      url: previewImageUrl,
    };
  }

  return null;
}

async function parseResponse<
  T extends object,
>(
  response: Response,
): Promise<T> {
  let data:
    | T
    | {
        message?: string;
      };

  try {
    data = (await response.json()) as
      | T
      | {
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
      "message" in data &&
      typeof data.message === "string"
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

  const response = await fetch(
    `${apiBaseUrl}/analyses`,
    {
      method: "POST",
      credentials: "include",
      body: formData,
    },
  );

  const data =
    await parseResponse<AnalysisResponse>(
      response,
    );

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
      credentials: "include",
    },
  );

  const data =
    await parseResponse<AnalysisResponse>(
      response,
    );

  return data.analysis;
}

export async function getAnalysisRecords(): Promise<
  AnalysisRecord[]
> {
  const response = await fetch(
    `${apiBaseUrl}/analyses`,
    {
      cache: "no-store",
      credentials: "include",
    },
  );

  const data =
    await parseResponse<AnalysesResponse>(
      response,
    );

  return data.analyses;
}

export async function deleteAnalysis(
  analysisId: string,
): Promise<string> {
  const response = await fetch(
    `${apiBaseUrl}/analyses/${encodeURIComponent(
      analysisId,
    )}`,
    {
      method: "DELETE",
      credentials: "include",
    },
  );

  const data =
    await parseResponse<MessageResponse>(
      response,
    );

  return data.message;
}

export async function getAnalysis(
  analysisId: string,
): Promise<SwingAnalysis> {
  const record =
    await getAnalysisRecord(
      analysisId,
    );

  if (record.status === "FAILED") {
    throw new Error(
      record.failureReason ??
        "The swing analysis failed.",
    );
  }

  if (
    record.status !== "COMPLETED"
  ) {
    throw new Error(
      "The swing analysis is not complete yet.",
    );
  }

  if (!record.analysisPayload) {
    throw new Error(
      "The completed swing analysis does not contain a public analysis payload.",
    );
  }

  return mapBackendAnalysis(
    record,
    apiOrigin,
  );
}