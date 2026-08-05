import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  AlertCircle,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileVideo2,
  Gauge,
  History,
  LoaderCircle,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";

import {
  deleteAnalysis,
  getAnalysisRecords,
  type AnalysisRecord,
  type AnalysisStatus,
} from "../services/analysisService";

type StatusDisplay = {
  label: string;
  className: string;
  icon: typeof Clock3;
};

type SortOption =
  | "newest"
  | "oldest"
  | "highest-score"
  | "lowest-score";

type DeleteConfirmationDialogProps = {
  analysis: AnalysisRecord;
  isDeleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
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

function formatDate(
  dateValue: string,
) {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    },
  ).format(date);
}

function formatTime(
  dateValue: string,
) {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Time unavailable";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(date);
}

function formatFilename(
  filename: string,
) {
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
    (character) =>
      character.toUpperCase(),
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

function compareScores(
  firstScore: number | null,
  secondScore: number | null,
  direction: "ascending" | "descending",
) {
  if (
    firstScore === null &&
    secondScore === null
  ) {
    return 0;
  }

  if (firstScore === null) {
    return 1;
  }

  if (secondScore === null) {
    return -1;
  }

  return direction === "ascending"
    ? firstScore - secondScore
    : secondScore - firstScore;
}

function DeleteConfirmationDialog({
  analysis,
  isDeleting,
  onCancel,
  onConfirm,
}: DeleteConfirmationDialogProps) {
  useEffect(() => {
    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (
        event.key === "Escape" &&
        !isDeleting
      ) {
        onCancel();
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [
    isDeleting,
    onCancel,
  ]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 px-4 py-8 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target ===
            event.currentTarget &&
          !isDeleting
        ) {
          onCancel();
        }
      }}
    >
      <div
        aria-describedby="delete-analysis-description"
        aria-labelledby="delete-analysis-title"
        aria-modal="true"
        className="w-full max-w-lg rounded-[1.75rem] border border-white/10 bg-[#101d16] p-6 shadow-2xl shadow-black/40 sm:p-8"
        role="dialog"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-red-400/20 bg-red-400/10 text-red-200">
            <Trash2 className="h-6 w-6" />
          </div>

          <button
            aria-label="Close delete confirmation"
            className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white/60 transition hover:bg-white/[0.08] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            disabled={isDeleting}
            type="button"
            onClick={onCancel}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <h2
          id="delete-analysis-title"
          className="mt-6 font-display text-2xl font-semibold tracking-[-0.035em] text-white"
        >
          Delete this analysis?
        </h2>

        <p
          id="delete-analysis-description"
          className="mt-3 text-sm leading-6 text-white/60"
        >
          You are about to permanently delete{" "}
          <span className="font-semibold text-white">
            {formatFilename(
              analysis.originalFilename,
            )}
          </span>
          . This action cannot be undone.
        </p>

        <div className="mt-6 rounded-2xl border border-white/10 bg-black/15 p-4">
          <p className="text-sm font-semibold text-white">
            TempoAI will permanently remove:
          </p>

          <div className="mt-4 space-y-3">
            {[
              "The uploaded swing video",
              "The analysis report and coaching results",
              "Published club visualization images",
            ].map((item) => (
              <div
                key={item}
                className="flex items-start gap-3"
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-red-200" />

                <p className="text-sm text-white/55">
                  {item}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/12 bg-white/[0.04] px-5 text-sm font-semibold text-white transition hover:bg-white/[0.08] disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isDeleting}
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>

          <button
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-red-400 px-5 text-sm font-semibold text-[#240707] transition hover:bg-red-300 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isDeleting}
            type="button"
            onClick={onConfirm}
          >
            {isDeleting ? (
              <>
                <LoaderCircle className="h-4 w-4 animate-spin" />
                Deleting
              </>
            ) : (
              <>
                <Trash2 className="h-4 w-4" />
                Delete analysis
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function HistoryPage() {
  const [analyses, setAnalyses] = useState<
    AnalysisRecord[]
  >([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [actionError, setActionError] =
    useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  const [requestVersion, setRequestVersion] =
    useState(0);

  const [searchQuery, setSearchQuery] =
    useState("");

  const [sortOption, setSortOption] =
    useState<SortOption>("newest");

  const [
    analysisPendingDeletion,
    setAnalysisPendingDeletion,
  ] = useState<AnalysisRecord | null>(
    null,
  );

  const [
    deletingAnalysisId,
    setDeletingAnalysisId,
  ] = useState<string | null>(null);

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

  const visibleAnalyses = useMemo(
    () => {
      const normalizedQuery =
        searchQuery
          .trim()
          .toLowerCase();

      const filteredAnalyses =
        normalizedQuery.length === 0
          ? analyses
          : analyses.filter(
              (analysis) => {
                const formattedName =
                  formatFilename(
                    analysis.originalFilename,
                  ).toLowerCase();

                return (
                  analysis.originalFilename
                    .toLowerCase()
                    .includes(
                      normalizedQuery,
                    ) ||
                  formattedName.includes(
                    normalizedQuery,
                  )
                );
              },
            );

      return [
        ...filteredAnalyses,
      ].sort(
        (
          firstAnalysis,
          secondAnalysis,
        ) => {
          if (
            sortOption === "oldest"
          ) {
            return (
              new Date(
                firstAnalysis.createdAt,
              ).getTime() -
              new Date(
                secondAnalysis.createdAt,
              ).getTime()
            );
          }

          if (
            sortOption ===
            "highest-score"
          ) {
            return compareScores(
              firstAnalysis.swingScore,
              secondAnalysis.swingScore,
              "descending",
            );
          }

          if (
            sortOption ===
            "lowest-score"
          ) {
            return compareScores(
              firstAnalysis.swingScore,
              secondAnalysis.swingScore,
              "ascending",
            );
          }

          return (
            new Date(
              secondAnalysis.createdAt,
            ).getTime() -
            new Date(
              firstAnalysis.createdAt,
            ).getTime()
          );
        },
      );
    },
    [
      analyses,
      searchQuery,
      sortOption,
    ],
  );

  function handleRetry() {
    setIsLoading(true);
    setError("");
    setActionError("");
    setSuccessMessage("");

    setRequestVersion(
      (currentVersion) =>
        currentVersion + 1,
    );
  }

  function openDeleteDialog(
    analysis: AnalysisRecord,
  ) {
    setActionError("");
    setSuccessMessage("");
    setAnalysisPendingDeletion(
      analysis,
    );
  }

  function closeDeleteDialog() {
    if (deletingAnalysisId) {
      return;
    }

    setAnalysisPendingDeletion(null);
  }

  async function handleDeleteAnalysis() {
    if (
      !analysisPendingDeletion ||
      deletingAnalysisId
    ) {
      return;
    }

    const analysisToDelete =
      analysisPendingDeletion;

    try {
      setActionError("");
      setSuccessMessage("");
      setDeletingAnalysisId(
        analysisToDelete.id,
      );

      const message =
        await deleteAnalysis(
          analysisToDelete.id,
        );

      setAnalyses(
        (currentAnalyses) =>
          currentAnalyses.filter(
            (analysis) =>
              analysis.id !==
              analysisToDelete.id,
          ),
      );

      setAnalysisPendingDeletion(
        null,
      );

      setSuccessMessage(message);
    } catch (deleteError) {
      setActionError(
        deleteError instanceof Error
          ? deleteError.message
          : "TempoAI could not delete this analysis.",
      );
    } finally {
      setDeletingAnalysisId(null);
    }
  }

  return (
    <>
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
                  Search your private swing
                  history, revisit coaching
                  recommendations, and manage
                  completed analyses.
                </p>
              </div>

              <Link
                className="inline-flex w-fit items-center justify-center gap-2 rounded-full bg-[#84ff4d] px-6 py-3.5 text-sm font-semibold !text-[#07110d] transition hover:bg-[#a0ff77] focus:outline-none focus:ring-2 focus:ring-[#84ff4d] focus:ring-offset-2 focus:ring-offset-[#07110d]"
                to="/analysis/new"
              >
                <Plus className="h-4 w-4" />
                Analyze new swing
              </Link>
            </div>
          </section>

          <section className="mt-8">
            {successMessage && (
              <div className="mb-5 flex items-start justify-between gap-4 rounded-2xl border border-[#84ff4d]/20 bg-[#84ff4d]/[0.07] p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[#84ff4d]" />

                  <p className="text-sm leading-6 text-[#caffb2]">
                    {successMessage}
                  </p>
                </div>

                <button
                  aria-label="Dismiss success message"
                  className="text-[#caffb2]/60 transition hover:text-[#caffb2]"
                  type="button"
                  onClick={() =>
                    setSuccessMessage("")
                  }
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}

            {actionError && (
              <div className="mb-5 flex items-start justify-between gap-4 rounded-2xl border border-red-400/20 bg-red-400/[0.07] p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-200" />

                  <p className="text-sm leading-6 text-red-100">
                    {actionError}
                  </p>
                </div>

                <button
                  aria-label="Dismiss error message"
                  className="text-red-200/60 transition hover:text-red-200"
                  type="button"
                  onClick={() =>
                    setActionError("")
                  }
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}

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
                  className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.06] px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
                  type="button"
                  onClick={handleRetry}
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
                  className="mt-7 inline-flex items-center gap-2 rounded-full bg-[#84ff4d] px-6 py-3 text-sm font-semibold text-[#07110d] transition hover:bg-[#a0ff77]"
                  to="/analysis/new"
                >
                  Analyze your first swing
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            ) : (
              <>
                <div className="mb-6 rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-4 sm:p-5">
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_14rem]">
                    <label className="block">
                      <span className="sr-only">
                        Search analyses
                      </span>

                      <div className="relative">
                        <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/35" />

                        <input
                          className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/15 py-3 pl-11 pr-4 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-[#84ff4d]/40 focus:ring-2 focus:ring-[#84ff4d]/15"
                          placeholder="Search analyses by filename"
                          type="search"
                          value={searchQuery}
                          onChange={(event) =>
                            setSearchQuery(
                              event.target.value,
                            )
                          }
                        />
                      </div>
                    </label>

                    <label className="block">
                      <span className="sr-only">
                        Sort analyses
                      </span>

                      <select
                        className="min-h-12 w-full rounded-2xl border border-white/10 bg-[#0d1913] px-4 text-sm font-semibold text-white outline-none transition focus:border-[#84ff4d]/40 focus:ring-2 focus:ring-[#84ff4d]/15"
                        value={sortOption}
                        onChange={(event) =>
                          setSortOption(
                            event.target
                              .value as SortOption,
                          )
                        }
                      >
                        <option value="newest">
                          Newest first
                        </option>

                        <option value="oldest">
                          Oldest first
                        </option>

                        <option value="highest-score">
                          Highest score
                        </option>

                        <option value="lowest-score">
                          Lowest score
                        </option>
                      </select>
                    </label>
                  </div>

                  <p className="mt-4 text-sm text-white/45">
                    Showing{" "}
                    {visibleAnalyses.length} of{" "}
                    {analyses.length}{" "}
                    {analyses.length === 1
                      ? "analysis"
                      : "analyses"}
                  </p>
                </div>

                {visibleAnalyses.length ===
                0 ? (
                  <div className="flex min-h-72 flex-col items-center justify-center rounded-[2rem] border border-dashed border-white/15 bg-white/[0.025] px-6 text-center">
                    <Search className="h-8 w-8 text-white/30" />

                    <h2 className="mt-5 text-xl font-semibold text-white">
                      No matching analyses
                    </h2>

                    <p className="mt-2 max-w-md text-sm leading-6 text-white/50">
                      Try a different filename or
                      clear your search to view your
                      complete swing history.
                    </p>

                    <button
                      className="mt-6 rounded-full border border-white/12 bg-white/[0.05] px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/[0.09]"
                      type="button"
                      onClick={() =>
                        setSearchQuery("")
                      }
                    >
                      Clear search
                    </button>
                  </div>
                ) : (
                  <div className="grid gap-5">
                    {visibleAnalyses.map(
                      (analysis) => {
                        const statusDisplay =
                          statusDisplays[
                            analysis.status
                          ];

                        const StatusIcon =
                          statusDisplay.icon;

                        const hasCompleted =
                          analysis.status ===
                          "COMPLETED";

                        const isProcessing =
                          analysis.status ===
                            "PROCESSING" ||
                          analysis.status ===
                            "UPLOADING";

                        const destination =
                          hasCompleted
                            ? `/analysis/${analysis.id}`
                            : analysis.status ===
                                "PROCESSING"
                              ? `/analysis/processing?analysisId=${encodeURIComponent(
                                  analysis.id,
                                )}`
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
                                          isProcessing
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

                                <div className="flex gap-3 sm:flex-col lg:flex-row">
                                  <Link
                                    className="inline-flex min-h-12 flex-1 items-center justify-center gap-2 rounded-full border border-white/12 bg-white/[0.06] px-5 text-sm font-semibold text-white transition group-hover:border-[#84ff4d]/25 group-hover:bg-[#84ff4d]/10 group-hover:text-[#b8ff97]"
                                    to={destination}
                                  >
                                    {hasCompleted ? (
                                      <>
                                        <Gauge className="h-4 w-4" />
                                        View
                                      </>
                                    ) : analysis.status ===
                                      "PROCESSING" ? (
                                      <>
                                        <LoaderCircle className="h-4 w-4 animate-spin" />
                                        Progress
                                      </>
                                    ) : (
                                      <>
                                        <RotateCcw className="h-4 w-4" />
                                        Retry
                                      </>
                                    )}

                                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                                  </Link>

                                  <button
                                    className="inline-flex min-h-12 flex-1 items-center justify-center gap-2 rounded-full border border-red-400/15 bg-red-400/[0.05] px-5 text-sm font-semibold text-red-200 transition hover:border-red-400/30 hover:bg-red-400/10 disabled:cursor-not-allowed disabled:border-white/8 disabled:bg-white/[0.025] disabled:text-white/25"
                                    disabled={
                                      isProcessing
                                    }
                                    title={
                                      isProcessing
                                        ? "Wait for processing to finish before deleting this analysis."
                                        : "Delete this analysis"
                                    }
                                    type="button"
                                    onClick={() =>
                                      openDeleteDialog(
                                        analysis,
                                      )
                                    }
                                  >
                                    <Trash2 className="h-4 w-4" />
                                    Delete
                                  </button>
                                </div>
                              </div>
                            </div>
                          </article>
                        );
                      },
                    )}
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </main>

      {analysisPendingDeletion && (
        <DeleteConfirmationDialog
          analysis={
            analysisPendingDeletion
          }
          isDeleting={
            deletingAnalysisId ===
            analysisPendingDeletion.id
          }
          onCancel={
            closeDeleteDialog
          }
          onConfirm={() =>
            void handleDeleteAnalysis()
          }
        />
      )}
    </>
  );
}

export default HistoryPage;