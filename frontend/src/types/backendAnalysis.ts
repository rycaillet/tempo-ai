export type BackendMetricKey =
  | "tempo"
  | "addressPosture"
  | "impactPosition"
  | "headStability"
  | "weightShift"
  | "earlyExtension"
  | "rotation"
  | "shaftLean"
  | "swingPlane";

export type BackendSeverity =
  | "high"
  | "medium"
  | "low";

export type BackendMetricScore = {
  reason?: string | null;
  status?: string;
  rawScore?: number;
  confidence?: number;
  classification?: string;
  configuredWeight?: number;
  normalizedWeight?: number;
  weightedContribution?: number;
};

export type BackendScoringInterpretation = {
  rating?: string;
  status?: string;
  summary?: string;
  warnings?: string[];
  strengths?: BackendMetricKey[];
  ratingLabel?: string;
  improvementPriorities?: BackendMetricKey[];
};

export type BackendScoring = {
  metrics?: Partial<
    Record<BackendMetricKey, BackendMetricScore>
  >;
  overallScore?: number;
  scoreCoverage?: number;
  weightedTotal?: number;
  interpretation?: BackendScoringInterpretation;
  possibleWeight?: number;
  availableWeight?: number;
  scoreConfidence?: number;
};

export type BackendFindingStrength = {
  score?: number;
  reason?: string;
  metricKey?: BackendMetricKey;
  displayName?: string;
};

export type BackendImprovementPriority = {
  score?: number;
  reason?: string;
  severity?: BackendSeverity;
  metricKey?: BackendMetricKey;
  displayName?: string;
};

export type BackendFindings = {
  status?: string;
  warnings?: string[];
  strengths?: BackendFindingStrength[];
  overallFinding?: string;
  improvementPriorities?: BackendImprovementPriority[];
};

export type BackendRecommendation = {
  focus?: string;
  title?: string;
  caution?: string;
  summary?: string;
  priority?: number;
  severity?: BackendSeverity;
  metricKey?: BackendMetricKey;
  rationale?: string;
  displayName?: string;
  practiceCues?: string[];
};

export type BackendRecommendations = {
  status?: string;
  warnings?: string[];
  primaryFocus?: {
    severity?: BackendSeverity;
    metricKey?: BackendMetricKey;
    displayName?: string;
  };
  recommendations?: BackendRecommendation[];
};

export type BackendPublicRecommendations = {
  status?: string;
  warnings?: string[];
  primaryFocus?: {
    severity?: BackendSeverity;
    metricKey?: BackendMetricKey;
    displayName?: string;
  } | null;
  items?: BackendRecommendation[];
};

export type BackendCoaching = {
  status?: string;
  headline?: string | null;
  overview?: string | null;
  warnings?: string[];
  disclaimer?: string | null;
  actionSteps?: string[];
  primaryFocus?: string | null;
  encouragement?: string | null;
};

export type BackendPhaseFrame = {
  frameIndex?: number;
  poseDetected?: boolean;
  timestampSeconds?: number;
};

export type BackendPhaseFrames = {
  addressReference?: BackendPhaseFrame;
  takeawayReference?: BackendPhaseFrame;
  topOfBackswing?: BackendPhaseFrame;
  downswingStart?: BackendPhaseFrame;
  impactReference?: BackendPhaseFrame;
  finishReference?: BackendPhaseFrame;
};

export type LegacyPhaseTimings = {
  address?: number;
  takeaway?: number;
  top?: number;
  downswing?: number;
  impact?: number;
  finish?: number;
};

export type BackendTempoMetric = {
  backswingToDownswingRatio?: number;
  ratio?: number;
  tempoRatio?: number;
  backswingDurationSeconds?: number;
  downswingDurationSeconds?: number;
  backswingSeconds?: number;
  downswingSeconds?: number;
  measurements?: {
    backswingDurationSeconds?: number;
    downswingDurationSeconds?: number;
  };
};

export type BackendAnalysisMetricCard = {
  metricKey?: BackendMetricKey;
  displayName?: string;
  score?: number | null;
  confidence?: number | null;
  scoreStatus?: string | null;
  weightedScore?: number | null;
  classification?: string | null;
  deliveryStatus?: string | null;
  feedbackStatus?: string | null;
  measurementCompleteness?: number | null;
};

export type BackendAnalysisPayload = {
  contractVersion?: string;
  status?: "ready" | "partial";
  score?: {
    overallScore?: number;
    confidence?: number;
    coverage?: number;
    rating?: string;
    ratingLabel?: string;
    status?: string;
    summary?: string;
  };
  metrics?: BackendAnalysisMetricCard[];
  coaching?: BackendCoaching | null;
  findings?: BackendFindings;
  recommendations?: BackendPublicRecommendations;
  limitations?: string[];
};

export type BackendAnalysisReport = {
  scoring?: BackendScoring;
  summary?: {
    tempoRatio?: number;
    tempoStatus?: string;
    tempoClassification?: string;
    rotationClassification?: string;
    weightShiftClassification?: string;
    headStabilityClassification?: string;
    addressPostureClassification?: string;
    earlyExtensionClassification?: string;
    impactPositionClassification?: string;
  };
  metrics?: {
    tempo?: BackendTempoMetric;
  };
  coaching?: BackendCoaching;
  findings?: BackendFindings;
  recommendations?: BackendRecommendations;
  phaseFrames?: BackendPhaseFrames;
};