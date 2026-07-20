import { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CalendarDays,
  Clock3,
  FileVideo2,
  Gauge,
  History,
  LoaderCircle,
  Plus,
  RefreshCw,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";

import {
  getAnalysisRecords,
  type AnalysisRecord,
  type AnalysisStatus,
} from "../services/analysisService";

type StatusDisplay = {
  label: string;
  className: string;
  icon: typeof Clock3;
};

const statusDisplays: Record<
  AnalysisStatus,
  StatusDisplay
> = {
  UPLOADING: {
    label: "Uploading",
    className:
      "border-sky-400/20 bg-sky-400/10 text-sky-200",
    icon: LoaderCircle,
  },
  PROCESSING: {
    label: "Processing",
    className:
      "border-amber-400/20 bg-amber-400/10 text-amber-200",
    icon: LoaderCircle,
  },
  COMPLETED: {
    label: "Completed",
    className:
      "border-[#84ff4d]/20 bg-[#84ff4d]/10 text-[#b8ff97]",
    icon: Sparkles,
  },
  FAILED: {
    label: "Failed",
    className:
      "border-red-400/20 bg-red-400/10 text-red-200",
    icon: AlertCircle,
  },
};

function formatDate(dateValue: string) {
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

function formatTime(dateValue: string) {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Time unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatFilename(filename: string) {
  const filenameWithoutExtension =
    filename.replace(/\.[^/.]+$/, "");

  const cleanedFilename =
    filenameWithoutExtension
      .replace(/[-_]+/g, " ")
      .trim();

  if (!cleanedFilename) {
    return "Golf Swing Analysis";
  }

  return cleanedFilename.replace(
    /\b\w/g,
    (character) => character.toUpperCase(),
  );
}

function formatFileSize(
  fileSizeBytes: number | null,
) {
  if (
    fileSizeBytes === null ||
    fileSizeBytes < 0
  ) {
    return "Size unavailable";
  }

  const megabytes =
    fileSizeBytes / (1024 * 1024);

  if (megabytes < 1) {
    const kilobytes =
      fileSizeBytes / 1024;

    return `${kilobytes.toFixed(0)} KB`;
  }

  return `${megabytes.toFixed(1)} MB`;
}

function HistoryPage() {
  const [analyses, setAnalyses] = useState<
    AnalysisRecord[]
  >([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] = useState("");
  const [requestVersion, setRequestVersion] =
    useState(0);

  useEffect(() => {
    let isActive = true;

    async function loadAnalyses() {
      try {
        const records =
          await getAnalysisRecords();

        if (!isActive) {
          return;
        }

        setAnalyses(records);
        setError("");
      } catch (loadError) {
        if (!isActive) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "TempoAI could not load your swing history.",
        );
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadAnalyses();

    return () => {
      isActive = false;
    };
  }, [requestVersion]);

  function handleRetry() {
    setIsLoading(true);
    setError("");
    setRequestVersion(
      (currentVersion) =>
        currentVersion + 1,
    );
  }

  return (
    <main className="min-h-screen bg-[#07110d] px-4 py-10 text-white sm:px-6 sm:py-14 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <section className="overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(132,255,77,0.13),transparent_35%),linear-gradient(135deg,rgba(17,38,29,0.96),rgba(8,20,15,0.96))] p-6 shadow-2xl shadow-black/20 sm:p-8 lg:p-10">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-[#84ff4d]">
                <History className="h-4 w-4" />
                Previous sessions
              </div>

              <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em] sm:text-5xl lg:text-6xl">
                Swing History
              </h1>

              <p className="mt-5 max-w-2xl text-base leading-7 text-white/60 sm:text-lg">
                Review previous swing analyses,
                compare your scores, and revisit
                coaching recommendations.
              </p>
            </div>

            <Link
              to="/analysis/new"
              className="inline-flex w-fit items-center justify-center gap-2 rounded-full bg-[#84ff4d] px-6 py-3.5 text-sm font-semibold !text-[#07110d] transition hover:bg-[#a0ff77] focus:outline-none focus:ring-2 focus:ring-[#84ff4d] focus:ring-offset-2 focus:ring-offset-[#07110d]"
            >
              <Plus className="h-4 w-4" />
              Analyze new swing
            </Link>
          </div>
        </section>

        <section className="mt-8">
          {isLoading ? (
            <div className="flex min-h-80 flex-col items-center justify-center rounded-[2rem] border border-white/10 bg-white/[0.035] px-6 text-center">
              <LoaderCircle className="h-9 w-9 animate-spin text-[#84ff4d]" />

              <h2 className="mt-5 text-xl font-semibold">
                Loading swing history
              </h2>

              <p className="mt-2 text-sm text-white/50">
                Retrieving your previous analyses.
              </p>
            </div>
          ) : error ? (
            <div className="flex min-h-80 flex-col items-center justify-center rounded-[2rem] border border-red-400/20 bg-red-400/[0.06] px-6 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-400/10 text-red-200">
                <AlertCircle className="h-7 w-7" />
              </div>

              <h2 className="mt-5 text-xl font-semibold">
                Swing history could not be
                loaded
              </h2>

              <p className="mt-2 max-w-lg text-sm leading-6 text-white/55">
                {error}
              </p>

              <button
                type="button"
                onClick={handleRetry}
                className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.06] px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                <RefreshCw className="h-4 w-4" />
                Try again
              </button>
            </div>
          ) : analyses.length === 0 ? (
            <div className="flex min-h-96 flex-col items-center justify-center rounded-[2rem] border border-dashed border-white/15 bg-white/[0.025] px-6 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-[#84ff4d]/15 bg-[#84ff4d]/10 text-[#84ff4d]">
                <FileVideo2 className="h-8 w-8" />
              </div>

              <h2 className="mt-6 text-2xl font-semibold tracking-tight">
                No swing analyses yet
              </h2>

              <p className="mt-3 max-w-md text-sm leading-6 text-white/55">
                Upload your first golf swing
                video to receive scores, timing
                metrics, and coaching feedback.
              </p>

              <Link
                to="/analysis/new"
                className="mt-7 inline-flex items-center gap-2 rounded-full bg-[#84ff4d] px-6 py-3 text-sm font-semibold text-[#07110d] transition hover:bg-[#a0ff77]"
              >
                Analyze your first swing
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-5 flex items-center justify-between gap-4">
                <p className="text-sm text-white/50">
                  {analyses.length}{" "}
                  {analyses.length === 1
                    ? "analysis"
                    : "analyses"}
                </p>

                <button
                  type="button"
                  onClick={handleRetry}
                  className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/70 transition hover:border-white/20 hover:bg-white/[0.07] hover:text-white"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </button>
              </div>

              <div className="grid gap-5">
                {analyses.map((analysis) => {
                  const statusDisplay =
                    statusDisplays[
                      analysis.status
                    ];

                  const StatusIcon =
                    statusDisplay.icon;

                  const hasCompleted =
                    analysis.status ===
                    "COMPLETED";

                  const destination =
                    hasCompleted
                      ? `/analysis/${analysis.id}`
                      : analysis.status ===
                          "PROCESSING"
                        ? `/analysis/processing/${analysis.id}`
                        : "/analysis/new";

                  return (
                    <article
                      key={analysis.id}
                      className="group overflow-hidden rounded-[1.75rem] border border-white/10 bg-white/[0.035] transition hover:border-[#84ff4d]/25 hover:bg-white/[0.05]"
                    >
                      <div className="grid gap-6 p-5 sm:p-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
                        <div className="flex min-w-0 gap-4">
                          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.05] text-[#84ff4d]">
                            <FileVideo2 className="h-6 w-6" />
                          </div>

                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-3">
                              <h2 className="truncate text-lg font-semibold tracking-tight sm:text-xl">
                                {formatFilename(
                                  analysis.originalFilename,
                                )}
                              </h2>

                              <span
                                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${statusDisplay.className}`}
                              >
                                <StatusIcon
                                  className={`h-3.5 w-3.5 ${
                                    analysis.status ===
                                      "PROCESSING" ||
                                    analysis.status ===
                                      "UPLOADING"
                                      ? "animate-spin"
                                      : ""
                                  }`}
                                />

                                {
                                  statusDisplay.label
                                }
                              </span>
                            </div>

                            <p className="mt-1 truncate text-sm text-white/45">
                              {
                                analysis.originalFilename
                              }
                            </p>

                            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-white/45">
                              <span className="inline-flex items-center gap-1.5">
                                <CalendarDays className="h-3.5 w-3.5" />
                                {formatDate(
                                  analysis.createdAt,
                                )}
                              </span>

                              <span className="inline-flex items-center gap-1.5">
                                <Clock3 className="h-3.5 w-3.5" />
                                {formatTime(
                                  analysis.createdAt,
                                )}
                              </span>

                              <span className="inline-flex items-center gap-1.5">
                                <FileVideo2 className="h-3.5 w-3.5" />
                                {formatFileSize(
                                  analysis.fileSizeBytes,
                                )}
                              </span>
                            </div>

                            {analysis.status ===
                              "FAILED" &&
                            analysis.failureReason ? (
                              <p className="mt-4 text-sm leading-6 text-red-200/80">
                                {
                                  analysis.failureReason
                                }
                              </p>
                            ) : null}
                          </div>
                        </div>

                        <div className="flex flex-col gap-4 sm:flex-row sm:items-center lg:justify-end">
                          <div className="grid grid-cols-3 gap-3">
                            <div className="min-w-20 rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-center">
                              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-white/35">
                                Score
                              </p>

                              <p className="mt-1 text-xl font-semibold text-white">
                                {analysis.swingScore ??
                                  "—"}
                              </p>
                            </div>

                            <div className="min-w-20 rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-center">
                              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-white/35">
                                Tempo
                              </p>

                              <p className="mt-1 text-xl font-semibold text-white">
                                {analysis.tempoRatio !==
                                null
                                  ? `${analysis.tempoRatio.toFixed(
                                      2,
                                    )}:1`
                                  : "—"}
                              </p>
                            </div>

                            <div className="min-w-20 rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-center">
                              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-white/35">
                                Consistency
                              </p>

                              <p className="mt-1 text-xl font-semibold text-white">
                                {analysis.consistencyScore ??
                                  "—"}
                              </p>
                            </div>
                          </div>

                          <Link
                            to={destination}
                            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-white/12 bg-white/[0.06] px-5 text-sm font-semibold text-white transition group-hover:border-[#84ff4d]/25 group-hover:bg-[#84ff4d]/10 group-hover:text-[#b8ff97]"
                          >
                            {hasCompleted ? (
                              <>
                                <Gauge className="h-4 w-4" />
                                View analysis
                              </>
                            ) : analysis.status ===
                              "PROCESSING" ? (
                              <>
                                <LoaderCircle className="h-4 w-4 animate-spin" />
                                View progress
                              </>
                            ) : (
                              <>
                                <RotateCcw className="h-4 w-4" />
                                Try another
                              </>
                            )}

                            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                          </Link>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

export default HistoryPage;