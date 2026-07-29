import { demoAnalysis } from "../data/analysis";
import type { AnalysisRecord } from "../services/analysisService";
import type {
  SwingAnalysis,
  SwingFinding,
  SwingMetric,
} from "../types/analysis";

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
  const withoutExtension = filename.replace(/\.[^/.]+$/, "");

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
  apiOrigin: string,
): string | null {
  if (!storedFilename) {
    return null;
  }

  return `${apiOrigin}/uploads/analyses/${encodeURIComponent(
    storedFilename,
  )}`;
}

function createTempoScore(tempoRatio: number) {
  const targetTempoRatio = 3;
  const scorePenaltyPerRatioPoint = 35;

  const tempoDifference = Math.abs(
    targetTempoRatio - tempoRatio,
  );

  return Math.max(
    0,
    Math.min(
      100,
      Math.round(
        100 -
          tempoDifference * scorePenaltyPerRatioPoint,
      ),
    ),
  );
}

function mapMetrics(
  record: AnalysisRecord,
): SwingMetric[] {
  return demoAnalysis.metrics.map((metric) => {
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
      return {
        ...metric,
        score: createTempoScore(record.tempoRatio),
        description: `${record.tempoRatio.toFixed(
          2,
        )}:1 backswing-to-downswing tempo ratio.`,
      };
    }

    return metric;
  });
}

function mapFindings(
  record: AnalysisRecord,
): SwingFinding[] {
  return demoAnalysis.findings.map(
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
}

function createCoachingSummary(
  record: AnalysisRecord,
) {
  return [
    record.primaryFinding,
    record.recommendation,
  ]
    .filter(
      (value): value is string => Boolean(value),
    )
    .join(" ");
}

export function mapBackendAnalysis(
  record: AnalysisRecord,
  apiOrigin: string,
): SwingAnalysis {
  const coachingSummary =
    createCoachingSummary(record);

  return {
    ...demoAnalysis,
    videoUrl: createVideoUrl(
      record.storedFilename,
      apiOrigin,
    ),
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
    metrics: mapMetrics(record),
    findings: mapFindings(record),
  };
}