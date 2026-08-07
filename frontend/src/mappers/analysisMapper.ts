import type { AnalysisRecord } from "../services/analysisService";
import type {
  ClubAnalysis,
  ClubVisualization,
  FindingSeverity,
  PhaseCoaching,
  PoseVariant,
  PracticePlanItem,
  SwingAnalysis,
  SwingFinding,
  SwingMetric,
  SwingPhase,
} from "../types/analysis";
import type {
  BackendAnalysisPayload,
  BackendAnalysisReport,
  BackendClubVisualization,
  BackendImprovementPriority,
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
  shaftLean: "Shaft Lean",
  swingPlane: "Swing Plane",
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
  shaftLean: "Impact",
  swingPlane: "Throughout Swing",
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
  shaftLean:
    "Measures the detected shaft direction relative to image vertical at impact.",
  swingPlane:
    "Measures the camera-relative shaft trajectory across reference phases.",
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

type PhaseDefinition = {
  id: PoseVariant;
  label: string;
  poseVariant: PoseVariant;
  frameKey: keyof BackendPhaseFrames;
  legacyKey: keyof LegacyPhaseTimings;
  findingAliases: string[];
};

const phaseDefinitions: PhaseDefinition[] = [
  {
    id: "address",
    label: "Address",
    poseVariant: "address",
    frameKey: "addressReference",
    legacyKey: "address",
    findingAliases: ["address"],
  },
  {
    id: "takeaway",
    label: "Takeaway",
    poseVariant: "takeaway",
    frameKey: "takeawayReference",
    legacyKey: "takeaway",
    findingAliases: ["takeaway"],
  },
  {
    id: "top",
    label: "Top",
    poseVariant: "top",
    frameKey: "topOfBackswing",
    legacyKey: "top",
    findingAliases: ["top", "backswing"],
  },
  {
    id: "downswing",
    label: "Downswing",
    poseVariant: "downswing",
    frameKey: "downswingStart",
    legacyKey: "downswing",
    findingAliases: [
      "downswing",
      "transition",
      "backswing and downswing",
    ],
  },
  {
    id: "impact",
    label: "Impact",
    poseVariant: "impact",
    frameKey: "impactReference",
    legacyKey: "impact",
    findingAliases: ["impact"],
  },
  {
    id: "finish",
    label: "Finish",
    poseVariant: "finish",
    frameKey: "finishReference",
    legacyKey: "finish",
    findingAliases: ["finish"],
  },
];

function clampScore(score: number) {
  return Math.min(
    100,
    Math.max(0, Math.round(score)),
  );
}

function formatAnalysisDate(dateValue: string) {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
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
    return "Swing Analysis";
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

function createPublicAssetUrl(
  assetPath: string | undefined,
  apiOrigin: string,
): string | null {
  if (!assetPath?.trim()) {
    return null;
  }

  const normalizedPath = assetPath.trim();

  if (/^https?:\/\//i.test(normalizedPath)) {
    return normalizedPath;
  }

  return `${apiOrigin}${
    normalizedPath.startsWith("/") ? "" : "/"
  }${normalizedPath}`;
}

function mapClubVisualization(
  visualization: BackendClubVisualization | undefined,
  apiOrigin: string,
): ClubVisualization | null {
  const imageUrl = createPublicAssetUrl(
    visualization?.imageUrl,
    apiOrigin,
  );

  if (!imageUrl) {
    return null;
  }

  return {
    imageUrl,
    frameIndex: normalizeOptionalNumber(
      visualization?.frameIndex,
    ),
    timestampSeconds: normalizeOptionalNumber(
      visualization?.timestampSeconds,
    ),
    confidence: normalizeOptionalNumber(
      visualization?.confidence,
    ),
    geometrySource:
      visualization?.geometrySource ?? null,
    detectionSource:
      visualization?.detectionSource ?? null,
  };
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
  reason: string | null | undefined,
  record: AnalysisRecord,
) {
  if (reason?.trim()) {
    return reason.trim();
  }

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
  const payloadMetrics =
    record.analysisPayload?.metrics ?? [];

  const payloadByKey = new Map(
    payloadMetrics.flatMap((metric) => {
      if (!metric.metricKey) {
        return [];
      }

      return [[metric.metricKey, metric] as const];
    }),
  );

  const mappedMetrics = metricOrder.flatMap(
    (metricKey): SwingMetric[] => {
      const metric = payloadByKey.get(metricKey);

      if (
        !metric ||
        typeof metric.score !== "number"
      ) {
        return [];
      }

      return [
        {
          id: metricKey,
          label:
            metric.displayName ??
            metricDisplayNames[metricKey],
          score: clampScore(metric.score),
          description: createMetricDescription(
            metricKey,
            metric.classification ?? undefined,
            null,
            record,
          ),
          phase: metricPhaseNames[metricKey],
          classification:
            formatClassification(
              metric.classification ??
                undefined,
            ),
          confidence: normalizeOptionalNumber(
            metric.confidence ??
              record.analysisReport?.scoring
                ?.metrics?.[metricKey]
                ?.confidence,
          ),
          measurementCompleteness:
            normalizeOptionalNumber(
              metric.measurementCompleteness,
            ),
          feedbackStatus:
            formatClassification(
              metric.feedbackStatus ??
                undefined,
            ),
          deliveryStatus:
            formatClassification(
              metric.deliveryStatus ??
                undefined,
            ),
          scoreStatus:
            formatClassification(
              metric.scoreStatus ??
                undefined,
            ),
          configuredWeight:
            normalizeOptionalNumber(
              record.analysisReport?.scoring
                ?.metrics?.[metricKey]
                ?.configuredWeight,
            ),
          weightedContribution:
            normalizeOptionalNumber(
              record.analysisReport?.scoring
                ?.metrics?.[metricKey]
                ?.weightedContribution ??
                metric.weightedScore,
            ),
        },
      ];
    },
  );

  if (mappedMetrics.length > 0) {
    return mappedMetrics;
  }

  const reportMetrics =
    record.analysisReport?.scoring?.metrics;

  const legacyMetrics = metricOrder.flatMap(
    (metricKey): SwingMetric[] => {
      const metric = reportMetrics?.[metricKey];

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
          score: clampScore(metric.rawScore),
          description: createMetricDescription(
            metricKey,
            metric.classification,
            metric.reason,
            record,
          ),
          phase: metricPhaseNames[metricKey],
          classification:
            formatClassification(
              metric.classification,
            ),
          confidence: normalizeOptionalNumber(
            metric.confidence,
          ),
          measurementCompleteness: null,
          feedbackStatus: null,
          deliveryStatus: null,
          scoreStatus:
            formatClassification(
              metric.status,
            ),
          configuredWeight:
            normalizeOptionalNumber(
              metric.configuredWeight,
            ),
          weightedContribution:
            normalizeOptionalNumber(
              metric.weightedContribution,
            ),
        },
      ];
    },
  );

  if (legacyMetrics.length > 0) {
    return legacyMetrics;
  }

  if (record.consistencyScore !== null) {
    return [
      {
        id: "consistency",
        label: "Swing Consistency",
        score: clampScore(
          record.consistencyScore,
        ),
        description:
          "Measures the repeatability and stability of the detected swing movement.",
        phase: "Overall Swing",
        classification: null,
        confidence: null,
        measurementCompleteness: null,
        feedbackStatus: null,
        deliveryStatus: null,
        scoreStatus: "Scored",
        configuredWeight: null,
        weightedContribution: null,
      },
    ];
  }

  return [];
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
    recommendation.focus ??
    "Use slow practice swings to rehearse the identified movement priority."
  );
}

function mapRecommendationToFinding(
  recommendation: BackendRecommendation,
  index: number,
): SwingFinding {
  const metricKey =
    recommendation.metricKey ?? "tempo";

  const displayName =
    recommendation.displayName ??
    metricDisplayNames[metricKey];

  return {
    id: `finding-${index + 1}`,
    metricKey,
    priority:
      recommendation.priority ?? index + 1,
    title:
      recommendation.title ??
      `Improve ${displayName}`,
    phase: metricPhaseNames[metricKey],
    severity: mapSeverity(
      recommendation.severity,
    ),
    evidence:
      recommendation.rationale ??
      recommendation.caution ??
      "The analysis engine identified this metric as an improvement priority.",
    explanation:
      recommendation.summary ??
      recommendation.focus ??
      "Improving this movement may support a more repeatable golf swing.",
    drill: {
      name:
        recommendation.focus ??
        `${displayName} Practice`,
      instructions:
        createFindingDrillInstructions(
          recommendation,
        ),
    },
  };
}

function mapPriorityToFinding(
  priority: BackendImprovementPriority,
  index: number,
  fallbackInstruction: string | null,
): SwingFinding {
  const metricKey =
    priority.metricKey ?? "tempo";

  const displayName =
    priority.displayName ??
    metricDisplayNames[metricKey];

  return {
    id: `finding-${index + 1}`,
    metricKey,
    priority: index + 1,
    title: `Improve ${displayName}`,
    phase: metricPhaseNames[metricKey],
    severity: mapSeverity(priority.severity),
    evidence:
      priority.reason ??
      "The scoring report identified this metric as an improvement priority.",
    explanation:
      priority.reason ??
      `The ${displayName.toLowerCase()} result has the greatest opportunity for improvement.`,
    drill: {
      name: `${displayName} Practice`,
      instructions:
        fallbackInstruction ??
        `Use slow-motion practice swings while focusing on ${displayName.toLowerCase()}.`,
    },
  };
}

function mapFindings(
  record: AnalysisRecord,
): SwingFinding[] {
  const payload = record.analysisPayload;

  const recommendations =
    payload?.recommendations?.items ??
    record.analysisReport?.recommendations?.recommendations;

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

  const improvementPriorities =
    payload?.findings?.improvementPriorities ??
    record.analysisReport?.findings?.improvementPriorities;

  if (
    improvementPriorities &&
    improvementPriorities.length > 0
  ) {
    return improvementPriorities.map(
      (priority, index) =>
        mapPriorityToFinding(
          priority,
          index,
          record.recommendation,
        ),
    );
  }

  if (
    record.primaryFinding ||
    record.recommendation
  ) {
    return [
      {
        id: "finding-1",
        metricKey: null,
        priority: 1,
        title:
          record.primaryFinding ??
          "Primary Swing Priority",
        phase: "Overall Swing",
        severity: "Medium",
        evidence:
          record.primaryFinding ??
          "The stored analysis identified an overall swing priority.",
        explanation:
          record.recommendation ??
          record.primaryFinding ??
          "Review the stored analysis feedback before the next practice session.",
        drill: {
          name: "Focused Rehearsal",
          instructions:
            record.recommendation ??
            "Use slow practice swings to rehearse the identified movement.",
        },
      },
    ];
  }

  return [];
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
    !Number.isFinite(timestamp) ||
    timestamp < 0
  ) {
    return "0s";
  }

  return `${timestamp
    .toFixed(2)
    .replace(/\.?0+$/, "")}s`;
}

function findPhaseFinding(
  phaseDefinition: PhaseDefinition,
  findings: SwingFinding[],
) {
  return findings.find((finding) => {
    const findingPhase =
      finding.phase.toLowerCase();

    return phaseDefinition.findingAliases.some(
      (alias) =>
        findingPhase.includes(
          alias.toLowerCase(),
        ),
    );
  });
}

function createPhaseCoaching(
  phaseDefinition: PhaseDefinition,
  findings: SwingFinding[],
  coachingSummary: string,
): PhaseCoaching {
  const finding = findPhaseFinding(
    phaseDefinition,
    findings,
  );

  return {
    headline:
      finding?.title ??
      `${phaseDefinition.label} checkpoint`,
    message:
      finding?.explanation ??
      coachingSummary,
    poseVariant: phaseDefinition.poseVariant,
    ...(finding
      ? { findingId: finding.id }
      : {}),
  };
}

function mapPhases(
  record: AnalysisRecord,
  findings: SwingFinding[],
  coachingSummary: string,
  apiOrigin: string,
): SwingPhase[] {
  const phaseFrames =
    getReportPhaseFrames(record);

  const legacyTimings =
    getLegacyPhaseTimings(record);

  return phaseDefinitions.map(
    (phaseDefinition) => ({
      id: phaseDefinition.id,
      label: phaseDefinition.label,
      timestamp: getPhaseTimestamp(
        phaseFrames?.[
          phaseDefinition.frameKey
        ],
        legacyTimings?.[
          phaseDefinition.legacyKey
        ],
      ),
      status: "complete",
      coaching: createPhaseCoaching(
        phaseDefinition,
        findings,
        coachingSummary,
      ),
      clubVisualization: mapClubVisualization(
        record.analysisPayload?.clubVisualizations?.[
          phaseDefinition.id
        ],
        apiOrigin,
      ),
    }),
  );
}

function createCoachingSummary(
  record: AnalysisRecord,
) {
  const payload = record.analysisPayload;
  const report = record.analysisReport;

  const storedSummary = [
    record.primaryFinding,
    record.recommendation,
  ]
    .filter(
      (value): value is string =>
        Boolean(value?.trim()),
    )
    .join(" ");

  return (
    payload?.coaching?.overview ??
    payload?.findings?.overallFinding ??
    payload?.score?.summary ??
    report?.coaching?.overview ??
    report?.findings?.overallFinding ??
    report?.scoring?.interpretation?.summary ??
    (storedSummary ||
      "The swing analysis completed successfully, but no detailed coaching summary was returned.")
  );
}

function createStrengthSummary(
  record: AnalysisRecord,
) {
  const strongestFinding =
    record.analysisPayload?.findings
      ?.strengths?.[0] ??
    record.analysisReport?.findings
      ?.strengths?.[0];

  if (strongestFinding) {
    if (
      strongestFinding.displayName &&
      typeof strongestFinding.score === "number"
    ) {
      return `${strongestFinding.displayName} was a strength in this swing, scoring ${clampScore(
        strongestFinding.score,
      )} out of 100.`;
    }

    if (strongestFinding.reason?.trim()) {
      return strongestFinding.reason.trim();
    }
  }

  const strengthKey =
    record.analysisReport?.scoring
      ?.interpretation?.strengths?.[0];

  if (strengthKey) {
    return `${metricDisplayNames[strengthKey]} was one of the strongest measured parts of this swing.`;
  }

  if (record.consistencyScore !== null) {
    return `Swing consistency scored ${clampScore(
      record.consistencyScore,
    )} out of 100.`;
  }

  return "No individual strength summary was returned for this analysis.";
}

function mapPracticePlan(
  payload: BackendAnalysisPayload | null,
  report: BackendAnalysisReport | null,
  storedRecommendation: string | null,
): PracticePlanItem[] {
  const recommendations =
    payload?.recommendations?.items ??
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
          "Begin with easy half-speed swings to establish rhythm, balance, and a comfortable range of motion before working on the measured priorities.",
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

  const actionSteps =
    payload?.coaching?.actionSteps?.filter(
      (actionStep) =>
        actionStep.trim().length > 0,
    ) ??
    report?.coaching?.actionSteps?.filter(
      (actionStep) =>
        actionStep.trim().length > 0,
    );

  if (actionSteps && actionSteps.length > 0) {
    return actionSteps.map(
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

  if (storedRecommendation?.trim()) {
    return [
      {
        label: "Primary focus",
        duration: "10 minutes",
        instructions:
          storedRecommendation.trim(),
      },
    ];
  }

  return [];
}

function normalizeOptionalNumber(
  value: number | null | undefined,
): number | null {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value)
  ) {
    return null;
  }

  return value;
}

function mapClubAnalysis(
  payload: BackendAnalysisPayload | null,
): ClubAnalysis | null {
  const shaftLean =
    payload?.clubMetrics?.shaftLean;

  const swingPlane =
    payload?.clubMetrics?.swingPlane;

  const quality =
    payload?.clubAnalysisQuality;

  if (!shaftLean && !swingPlane && !quality) {
    return null;
  }

  const limitations =
    payload?.limitations?.filter(
      (limitation) =>
        limitation.trim().length > 0 &&
        (
          limitation
            .toLowerCase()
            .includes("shaft") ||
          limitation
            .toLowerCase()
            .includes("plane") ||
          limitation
            .toLowerCase()
            .includes("camera") ||
          limitation
            .toLowerCase()
            .includes("three-dimensional")
        ),
    ) ?? [];

  return {
    shaftLean: {
      available:
        shaftLean?.classification === "observed",
      angleDegrees: normalizeOptionalNumber(
        shaftLean
          ?.signedLeanFromVerticalDegrees,
      ),
      direction:
        shaftLean?.cameraRelativeDirection ??
        null,
      geometrySource:
        shaftLean?.geometrySource ?? null,
      confidence: normalizeOptionalNumber(
        shaftLean?.confidence,
      ),
      classification:
        shaftLean?.classification ?? null,
    },

    swingPlane: {
      available:
        swingPlane?.classification === "observed",
      confidence: normalizeOptionalNumber(
        swingPlane?.confidence,
      ),
      classification:
        swingPlane?.classification ?? null,
      measurementCompleteness:
        normalizeOptionalNumber(
          swingPlane
            ?.measurementCompleteness,
        ),
      smoothedReferenceCount:
        normalizeOptionalNumber(
          swingPlane
            ?.smoothedReferenceCount,
        ),
      trackedReferenceCount:
        normalizeOptionalNumber(
          swingPlane
            ?.trackedReferenceCount,
        ),
      topToImpactDegrees:
        normalizeOptionalNumber(
          swingPlane
            ?.phaseChangesDegrees
            ?.topToImpactDegrees,
        ),
    },

    quality: {
      status: quality?.status ?? null,
      detectionRate: normalizeOptionalNumber(
        quality?.detectionRate,
      ),
      detectedFrames: normalizeOptionalNumber(
        quality?.detectedFrames,
      ),
      requestedFrames: normalizeOptionalNumber(
        quality?.requestedFrames,
      ),
      referencePhasesAvailable:
        normalizeOptionalNumber(
          quality?.referencePhasesAvailable,
        ),
      referencePhasesTotal:
        normalizeOptionalNumber(
          quality?.referencePhasesTotal,
        ),
      minimumReferenceConfidence:
        normalizeOptionalNumber(
          quality?.minimumReferenceConfidence,
        ),
      usesTrackedGeometry:
        quality?.usesTrackedGeometry === true,
      usesSmoothedGeometry:
        quality?.usesSmoothedGeometry === true,
      warnings:
        quality?.warnings?.filter(
          (warning) =>
            warning.trim().length > 0,
        ) ?? [],
    },

    limitations,
  };
}

export function mapBackendAnalysis(
  record: AnalysisRecord,
  apiOrigin: string,
): SwingAnalysis {
  const coachingSummary =
    createCoachingSummary(record);

  const findings = mapFindings(record);

  const overallScore =
    record.analysisPayload?.score
      ?.overallScore ??
    record.analysisReport?.scoring
      ?.overallScore ??
    record.swingScore ??
    record.consistencyScore ??
    0;

  return {
    videoUrl: createVideoUrl(
      record.storedFilename,
      apiOrigin,
    ),
    videoMimeType: record.mimeType,
    summary: {
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
      overallScore:
        clampScore(overallScore),
      ratingLabel:
        record.analysisPayload?.score?.ratingLabel ??
        record.analysisReport?.scoring
          ?.interpretation?.ratingLabel ??
        null,
      summary: coachingSummary,
      strength:
        createStrengthSummary(record),
    },
    phases: mapPhases(
      record,
      findings,
      coachingSummary,
      apiOrigin,
    ),
    metrics: mapMetrics(record),
    clubAnalysis: mapClubAnalysis(
      record.analysisPayload,
    ),
    findings,
    practicePlan: mapPracticePlan(
      record.analysisPayload,
      record.analysisReport,
      record.recommendation,
    ),
  };
}