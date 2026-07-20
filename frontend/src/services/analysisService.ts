import { demoAnalysis } from "../data/analysis";
import type { SwingAnalysis } from "../types/analysis";

function delay(ms: number) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export async function getAnalysis(
  swingId: string,
): Promise<SwingAnalysis> {
  console.log("Loading analysis:", swingId);

  await delay(900);

  return {
    ...demoAnalysis,
    summary: {
      ...demoAnalysis.summary,
      id: swingId,
    },
  };
}