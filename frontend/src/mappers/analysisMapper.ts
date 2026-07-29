import { demoAnalysis } from "../data/analysis";
import type { AnalysisRecord } from "../services/analysisService";
import type {
  FindingSeverity,
  PracticePlanItem,
  SwingAnalysis,
  SwingFinding,
  SwingMetric,
  SwingPhase,
} from "../types/analysis";
import type {
  BackendAnalysisReport,
  BackendMetricKey,
  BackendPhaseFrame,
  BackendPhaseFrames,
  BackendRecommendation,
  BackendSeverity,
  LegacyPhaseTimings,
} from "../types/backendAnalysis";

const metricDisplayNames: Record<
  BackendMetricKey,
  string
> = {
  tempo: "Tempo",
  addressPosture: "Address Posture",
  impactPosition: "Impact Position",
  headStability: "Head Stability",
  weightShift: "Weight Shift",
  earlyExtension: "Early Extension",
  rotation: "Rotation",
};

const metricPhaseNames: Record<
  BackendMetricKey,
  string
> = {
  tempo: "Transition",
  addressPosture: "Address",
  impactPosition: "Impact",
  headStability: "Throughout Swing",
  weightShift: "Downswing",
  earlyExtension: "Downswing",
  rotation: "Backswing and Downswing",
};

const metricDescriptions: Record<
  BackendMetricKey,
  string
> = {
  tempo:
    "Measures the timing relationship between the backswing and downswing.",
  addressPosture:
    "Evaluates balance, alignment, and body posture at address.",
  impactPosition:
    "Evaluates body position and stability through impact.",
  headStability:
    "Measures head movement relative to the address position.",
  weightShift:
    "Evaluates lower-body movement and pressure-transfer patterns.",
  earlyExtension:
    "Measures whether the hips move toward the ball during the downswing.",
  rotation:
    "Evaluates measured shoulder and hip movement through the swing.",
};

const metricOrder: BackendMetricKey[] = [
  "addressPosture",
  "rotation",
  "tempo",
  "weightShift",
  "headStability",
  "earlyExtension",
  "impactPosition",
];

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

  return cleanedName.replace(
    /\b\w/g,
    (character) => character.toUpperCase(),
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

function formatClassification(
  classification: string | undefined,
) {
  if (!classification) {
    return null;
  }

  return classification
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function getTempoRatio(
  record: AnalysisRecord,
): number | null {
  const reportTempo =
    record.analysisReport?.metrics?.tempo;

  return (
    reportTempo?.backswingToDownswingRatio ??
    reportTempo?.ratio ??
    reportTempo?.tempoRatio ??
    record.analysisReport?.summary?.tempoRatio ??
    record.tempoRatio
  );
}

function createMetricDescription(
  metricKey: BackendMetricKey,
  classification: string | undefined,
  record: AnalysisRecord,
) {
  const classificationLabel =
    formatClassification(classification);

  if (metricKey === "tempo") {
    const tempoRatio = getTempoRatio(record);

    if (tempoRatio !== null) {
      const classificationText =
        classificationLabel !== null
          ? ` Classified as ${classificationLabel.toLowerCase()}.`
          : "";

      return `${tempoRatio.toFixed(
        2,
      )}:1 backswing-to-downswing ratio.${classificationText}`;
    }
  }

  if (classificationLabel) {
    return `${metricDescriptions[metricKey]} Result: ${classificationLabel}.`;
  }

  return metricDescriptions[metricKey];
}

function mapMetrics(
  record: AnalysisRecord,
): SwingMetric[] {
  const reportMetrics =
    record.analysisReport?.scoring?.metrics;

  if (!reportMetrics) {
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

      return metric;
    });
  }

  return metricOrder.flatMap((metricKey) => {
    const metric = reportMetrics[metricKey];

    if (
      !metric ||
      typeof metric.rawScore !== "number"
    ) {
      return [];
    }

    return [
      {
        id: metricKey,
        label: metricDisplayNames[metricKey],
        score: Math.round(metric.rawScore),
        description: createMetricDescription(
          metricKey,
          metric.classification,
          record,
        ),
      },
    ];
  });
}

function mapSeverity(
  severity: BackendSeverity | undefined,
): FindingSeverity {
  switch (severity) {
    case "high":
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
    default:
      return "Medium";
  }
}

function createFindingDrillInstructions(
  recommendation: BackendRecommendation,
) {
  const practiceCues =
    recommendation.practiceCues?.filter(
      (cue) => cue.trim().length > 0,
    ) ?? [];

  if (practiceCues.length > 0) {
    return practiceCues.join(" ");
  }

  return (
    recommendation.summary ??
    recommendation.rationale ??
    "Use slow practice swings to rehearse this movement pattern."
  );
}

function mapRecommendationToFinding(
  recommendation: BackendRecommendation,
  index: number,
): SwingFinding {
  const metricKey =
    recommendation.metricKey ?? "tempo";

  return {
    id: `finding-${index + 1}`,
    priority:
      recommendation.priority ?? index + 1,
    title:
      recommendation.title ??
      `Improve ${
        recommendation.displayName ??
        metricDisplayNames[metricKey]
      }`,
    phase: metricPhaseNames[metricKey],
    severity: mapSeverity(
      recommendation.severity,
    ),
    evidence:
      recommendation.rationale ??
      recommendation.caution ??
      "The analysis engine identified this as an improvement priority.",
    explanation:
      recommendation.summary ??
      recommendation.focus ??
      "Improving this movement may support a more repeatable golf swing.",
    drill: {
      name:
        recommendation.focus ??
        `${
          recommendation.displayName ??
          metricDisplayNames[metricKey]
        } Practice`,
      instructions:
        createFindingDrillInstructions(
          recommendation,
        ),
    },
  };
}

function mapFindings(
  record: AnalysisRecord,
): SwingFinding[] {
  const recommendations =
    record.analysisReport?.recommendations
      ?.recommendations;

  if (
    recommendations &&
    recommendations.length > 0
  ) {
    return [...recommendations]
      .sort(
        (left, right) =>
          (left.priority ?? 999) -
          (right.priority ?? 999),
      )
      .map(mapRecommendationToFinding);
  }

  return demoAnalysis.findings.map(
    (finding, index) => {
      if (index !== 0) {
        return finding;
      }

      return {
        ...finding,
        title:
          record.primaryFinding ??
          finding.title,
        explanation:
          record.recommendation ??
          finding.explanation,
      };
    },
  );
}

function isBackendPhaseFrames(
  value:
    | BackendPhaseFrames
    | LegacyPhaseTimings
    | null,
): value is BackendPhaseFrames {
  if (!value) {
    return false;
  }

  return Object.values(value).some(
    (phaseValue) =>
      typeof phaseValue === "object" &&
      phaseValue !== null,
  );
}

function getReportPhaseFrames(
  record: AnalysisRecord,
): BackendPhaseFrames | null {
  if (record.analysisReport?.phaseFrames) {
    return record.analysisReport.phaseFrames;
  }

  if (isBackendPhaseFrames(record.phaseTimings)) {
    return record.phaseTimings;
  }

  return null;
}

function getLegacyPhaseTimings(
  record: AnalysisRecord,
): LegacyPhaseTimings | null {
  if (
    !record.phaseTimings ||
    isBackendPhaseFrames(record.phaseTimings)
  ) {
    return null;
  }

  return record.phaseTimings;
}

function getPhaseTimestamp(
  frame: BackendPhaseFrame | undefined,
  legacyTimestamp: number | undefined,
) {
  const timestamp =
    frame?.timestampSeconds ??
    legacyTimestamp;

  if (
    typeof timestamp !== "number" ||
    !Number.isFinite(timestamp)
  ) {
    return null;
  }

  return `${timestamp
    .toFixed(2)
    .replace(/\.?0+$/, "")}s`;
}

function mapPhases(
  record: AnalysisRecord,
): SwingPhase[] {
  const phaseFrames =
    getReportPhaseFrames(record);
  const legacyTimings =
    getLegacyPhaseTimings(record);

  const timestamps: Record<
    SwingPhase["id"],
    string | null
  > = {
    address: getPhaseTimestamp(
      phaseFrames?.addressReference,
      legacyTimings?.address,
    ),
    takeaway: getPhaseTimestamp(
      phaseFrames?.takeawayReference,
      legacyTimings?.takeaway,
    ),
    top: getPhaseTimestamp(
      phaseFrames?.topOfBackswing,
      legacyTimings?.top,
    ),
    downswing: getPhaseTimestamp(
      phaseFrames?.downswingStart,
      legacyTimings?.downswing,
    ),
    impact: getPhaseTimestamp(
      phaseFrames?.impactReference,
      legacyTimings?.impact,
    ),
    finish: getPhaseTimestamp(
      phaseFrames?.finishReference,
      legacyTimings?.finish,
    ),
  };

  return demoAnalysis.phases.map((phase) => ({
    ...phase,
    timestamp:
      timestamps[phase.id] ??
      phase.timestamp,
  }));
}

function createCoachingSummary(
  record: AnalysisRecord,
) {
  const report = record.analysisReport;

  return (
    report?.coaching?.overview ??
    report?.findings?.overallFinding ??
    report?.scoring?.interpretation?.summary ??
    [record.primaryFinding, record.recommendation]
      .filter(
        (value): value is string =>
          Boolean(value),
      )
      .join(" ")
  );
}

function createStrengthSummary(
  record: AnalysisRecord,
) {
  const strongestFinding =
    record.analysisReport?.findings
      ?.strengths?.[0];

  if (strongestFinding) {
    if (
      strongestFinding.displayName &&
      typeof strongestFinding.score === "number"
    ) {
      return `${strongestFinding.displayName} was a strength in this swing, scoring ${Math.round(
        strongestFinding.score,
      )} out of 100.`;
    }

    if (strongestFinding.reason) {
      return strongestFinding.reason;
    }
  }

  const strengthKey =
    record.analysisReport?.scoring
      ?.interpretation?.strengths?.[0];

  if (strengthKey) {
    return `${metricDisplayNames[strengthKey]} was one of the strongest measured parts of this swing.`;
  }

  if (record.consistencyScore !== null) {
    return `Your swing consistency scored ${record.consistencyScore} out of 100.`;
  }

  return demoAnalysis.summary.strength;
}

function mapPracticePlan(
  report: BackendAnalysisReport | null,
): PracticePlanItem[] {
  const recommendations =
    report?.recommendations?.recommendations;

  if (
    recommendations &&
    recommendations.length > 0
  ) {
    const recommendationItems =
      [...recommendations]
        .sort(
          (left, right) =>
            (left.priority ?? 999) -
            (right.priority ?? 999),
        )
        .map(
          (
            recommendation,
            index,
          ): PracticePlanItem => ({
            label:
              recommendation.title ??
              recommendation.displayName ??
              `Practice priority ${index + 1}`,
            duration:
              index === 0
                ? "10 minutes"
                : "5 minutes",
            instructions:
              createFindingDrillInstructions(
                recommendation,
              ),
          }),
        );

    return [
      {
        label: "Warm-up",
        duration: "5 minutes",
        instructions:
          report?.coaching?.actionSteps?.join(
            " ",
          ) ??
          "Begin with slow-motion rehearsals of the primary movement priority.",
      },
      ...recommendationItems,
      {
        label: "Recording checkpoint",
        duration: "Final 5 swings",
        instructions:
          "Record five swings from the same camera position and compare the next analysis with this result.",
      },
    ];
  }

  if (
    report?.coaching?.actionSteps &&
    report.coaching.actionSteps.length > 0
  ) {
    return report.coaching.actionSteps.map(
      (actionStep, index) => ({
        label:
          index === 0
            ? "Primary focus"
            : `Practice cue ${index + 1}`,
        duration:
          index === 0
            ? "10 minutes"
            : "5 minutes",
        instructions: actionStep,
      }),
    );
  }

  return demoAnalysis.practicePlan;
}

export function mapBackendAnalysis(
  record: AnalysisRecord,
  apiOrigin: string,
): SwingAnalysis {
  const coachingSummary =
    createCoachingSummary(record);

  const overallScore =
    record.analysisReport?.scoring
      ?.overallScore ??
    record.swingScore ??
    demoAnalysis.summary.overallScore;

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
      club: null,
      cameraAngle: null,
      change: null,
      date: formatAnalysisDate(
        record.createdAt,
      ),
      overallScore: Math.round(overallScore),
      summary:
        coachingSummary ||
        demoAnalysis.summary.summary,
      strength:
        createStrengthSummary(record),
    },
    phases: mapPhases(record),
    metrics: mapMetrics(record),
    findings: mapFindings(record),
    practicePlan: mapPracticePlan(
      record.analysisReport,
    ),
  };
}