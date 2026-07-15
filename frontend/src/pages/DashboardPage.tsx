import { useEffect, useState } from "react";

import { getHealthStatus } from "../lib/api";
import type { HealthResponse } from "../types/health";

function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadHealthStatus() {
      try {
        const result = await getHealthStatus();
        setHealth(result);
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to connect to the API.",
        );
      }
    }

    void loadHealthStatus();
  }, []);

  return (
    <main className="min-h-screen bg-[#07110d] px-6 py-16 text-white">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#84ff4d]">
          Performance overview
        </p>

        <h1 className="mt-4 text-5xl font-semibold tracking-[-0.05em]">
          Dashboard
        </h1>

        <p className="mt-4 max-w-xl text-slate-400">
          Your swing activity, improvement trends, and recent coaching insights
          will appear here.
        </p>

        <div className="mt-10 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm">
          <span
            className={`size-2 rounded-full ${
              health ? "bg-[#84ff4d]" : error ? "bg-red-400" : "bg-amber-300"
            }`}
          />

          <span className="text-slate-300">
            {health
              ? `${health.service} connected`
              : error || "Checking API connection..."}
          </span>
        </div>
      </div>
    </main>
  );
}

export default DashboardPage;