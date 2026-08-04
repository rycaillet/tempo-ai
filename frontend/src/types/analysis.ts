export type SwingPhaseStatus = "complete" | "active";

export type FindingSeverity = "High" | "Medium" | "Low";

export type SwingPhase = {
  id: string;
  label: string;
  timestamp: string;
  status: SwingPhaseStatus;
  coaching: PhaseCoaching;
};

export type SwingMetric = {
  id: string;
  label: string;
  score: number;
  description: string;
};

export type SwingDrill = {
  name: string;
  instructions: string;
};

export type SwingFinding = {
  id: string;
  priority: number;
  title: string;
  phase: string;
  severity: FindingSeverity;
  evidence: string;
  explanation: string;
  drill: SwingDrill;
};

export type PracticePlanItem = {
  label: string;
  duration: string;
  instructions: string;
};

export type AnalysisSummary = {
  id: string;
  title: string;
  club: string | null;
  cameraAngle: string | null;
  date: string;
  overallScore: number;
  ratingLabel: string | null;
  change: string | null;
  summary: string;
  strength: string;
};

export type ShaftLeanObservation = {
  available: boolean;
  angleDegrees: number | null;
  direction: string | null;
  geometrySource: string | null;
  confidence: number | null;
  classification: string | null;
};

export type SwingPlaneObservation = {
  available: boolean;
  confidence: number | null;
  classification: string | null;
  measurementCompleteness: number | null;
  smoothedReferenceCount: number | null;
  trackedReferenceCount: number | null;
  topToImpactDegrees: number | null;
};

export type ClubAnalysisQuality = {
  status: string | null;
  detectionRate: number | null;
  detectedFrames: number | null;
  requestedFrames: number | null;
  referencePhasesAvailable: number | null;
  referencePhasesTotal: number | null;
  minimumReferenceConfidence: number | null;
  usesTrackedGeometry: boolean;
  usesSmoothedGeometry: boolean;
  warnings: string[];
};

export type ClubAnalysis = {
  shaftLean: ShaftLeanObservation;
  swingPlane: SwingPlaneObservation;
  quality: ClubAnalysisQuality;
  limitations: string[];
};

export type SwingAnalysis = {
  summary: AnalysisSummary;
  videoUrl: string | null;
  videoMimeType: string | null;
  phases: SwingPhase[];
  metrics: SwingMetric[];
  clubAnalysis: ClubAnalysis | null;
  findings: SwingFinding[];
  practicePlan: PracticePlanItem[];
};

export type PoseVariant =
  | "address"
  | "takeaway"
  | "top"
  | "downswing"
  | "impact"
  | "finish";

export type PhaseCoaching = {
  headline: string;
  message: string;
  poseVariant: PoseVariant;
  findingId?: string;
};