export type PhaseTimings = {
  address: number;
  takeaway: number;
  top: number;
  downswing: number;
  impact: number;
  finish: number;
};

export type GeneratedAnalysisResult = {
  swingScore: number;
  tempoRatio: number;
  backswingSeconds: number;
  downswingSeconds: number;
  consistencyScore: number;
  primaryFinding: string;
  recommendation: string;
  phaseTimings: PhaseTimings;
};

function roundSeconds(seconds: number) {
  return Number(seconds.toFixed(2));
}

function createEstimatedPhaseTimings(
  backswingSeconds: number,
  downswingSeconds: number,
): PhaseTimings {
  const takeawaySeconds =
    backswingSeconds * 0.45;

  const topSeconds = backswingSeconds;

  const downswingPhaseSeconds =
    backswingSeconds +
    downswingSeconds * 0.45;

  const impactSeconds =
    backswingSeconds + downswingSeconds;

  const finishSeconds =
    impactSeconds + 0.65;

  return {
    address: 0,
    takeaway: roundSeconds(takeawaySeconds),
    top: roundSeconds(topSeconds),
    downswing: roundSeconds(
      downswingPhaseSeconds,
    ),
    impact: roundSeconds(impactSeconds),
    finish: roundSeconds(finishSeconds),
  };
}

export function generateAnalysisResult(): GeneratedAnalysisResult {
  const backswingSeconds = 0.73;
  const downswingSeconds = 0.25;

  return {
    swingScore: 87,
    tempoRatio: 2.92,
    backswingSeconds,
    downswingSeconds,
    consistencyScore: 82,
    primaryFinding:
      "Early hip rotation during the downswing",
    recommendation:
      "Keep your chest closed slightly longer while starting the downswing from the lower body.",
    phaseTimings: createEstimatedPhaseTimings(
      backswingSeconds,
      downswingSeconds,
    ),
  };
}