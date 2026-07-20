import { completeAnalysis } from "./analysis.service.js";

const PROCESSING_DELAY_MS = 3000;

export function startAnalysisProcessing(analysisId: string) {
  setTimeout(() => {
    void completeAnalysis(analysisId).catch((error: unknown) => {
      console.error(`Failed to complete analysis ${analysisId}:`, error);
    });
  }, PROCESSING_DELAY_MS);
}