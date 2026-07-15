import type { HealthResponse } from "../types/health";

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:5001";

export async function getHealthStatus(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`);

  if (!response.ok) {
    throw new Error("Unable to connect to the TempoAI API.");
  }

  return response.json() as Promise<HealthResponse>;
}