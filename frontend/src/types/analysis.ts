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
  club: string;
  cameraAngle: string;
  date: string;
  overallScore: number;
  change: string;
  summary: string;
  strength: string;
};

export type SwingAnalysis = {
  summary: AnalysisSummary;
  phases: SwingPhase[];
  metrics: SwingMetric[];
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