import {
  Activity,
  ArrowRight,
  CalendarDays,
  CircleAlert,
  Clock3,
  FileVideo2,
  Gauge,
  LoaderCircle,
  Play,
  Sparkles,
  Target,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import MetricCard from "../components/ui/MetricCard";
import PageHeader from "../components/ui/PageHeader";
import Panel from "../components/ui/Panel";
import ScoreRing from "../components/ui/ScoreRing";
import Section from "../components/ui/Section";
import { useAuth } from "../hooks/useAuth";
import {
  getAnalysisRecords,
  type AnalysisRecord,
} from "../services/analysisService";

function formatDate(
  dateValue: string,
): string {
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

function formatFilename(
  filename: string,
): string {
  const nameWithoutExtension =
    filename.replace(/\.[^/.]+$/, "");

  const cleanedName =
    nameWithoutExtension
      .replace(/[-_]+/g, " ")
      .trim();

  if (!cleanedName) {
    return "Golf Swing Analysis";
  }

  return cleanedName.replace(
    /\b\w/g,
    (character) =>
      character.toUpperCase(),
  );
}

function averageValues(
  values: number[],
): number | null {
  if (values.length === 0) {
    return null;
  }

  return (
    values.reduce(
      (total, value) =>
        total + value,
      0,
    ) / values.length
  );
}

function DashboardPage() {
  const { user } = useAuth();

  const [analyses, setAnalyses] =
    useState<AnalysisRecord[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    let isActive = true;

    async function loadDashboard() {
      try {
        const records =
          await getAnalysisRecords();

        if (!isActive) {
          return;
        }

        setAnalyses(records);
        setError("");
      } catch (caughtError) {
        if (!isActive) {
          return;
        }

        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "TempoAI could not load your dashboard.",
        );
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      isActive = false;
    };
  }, []);

  const completedAnalyses = useMemo(
    () =>
      analyses.filter(
        (analysis) =>
          analysis.status ===
          "COMPLETED",
      ),
    [analyses],
  );

  const recentAnalyses =
    completedAnalyses.slice(0, 3);

  const latestAnalysis =
    completedAnalyses[0] ?? null;

  const averageTempo = averageValues(
    completedAnalyses
      .map(
        (analysis) =>
          analysis.tempoRatio,
      )
      .filter(
        (value): value is number =>
          value !== null,
      ),
  );

  const averageConsistency =
    averageValues(
      completedAnalyses
        .map(
          (analysis) =>
            analysis.consistencyScore,
        )
        .filter(
          (value): value is number =>
            value !== null,
        ),
    );

  const latestScore =
    latestAnalysis?.swingScore ?? 0;

  const hasCompletedAnalyses =
    completedAnalyses.length > 0;

  const firstName =
    user?.displayName
      .trim()
      .split(/\s+/)[0] ||
    "Golfer";

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="wide">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <PageHeader
              eyebrow="Performance overview"
              title={`Welcome back, ${firstName}.`}
              description={
                hasCompletedAnalyses
                  ? "Review your latest swing data, track your progress, and continue building a more repeatable golf swing."
                  : "Upload your first golf swing to begin building a private performance history."
              }
            />

            <Button
              size="lg"
              to="/analysis/new"
            >
              Analyze a new swing
              <ArrowRight size={18} />
            </Button>
          </div>

          {isLoading ? (
            <Panel
              className="mt-14 flex min-h-96 flex-col items-center justify-center text-center"
              padding="lg"
              variant="raised"
            >
              <LoaderCircle
                className="animate-spin text-lime-soft"
                size={34}
              />

              <p className="mt-5 font-display text-xl font-semibold text-white">
                Loading your dashboard
              </p>

              <p className="mt-2 text-sm text-copy-muted">
                Retrieving your private swing history.
              </p>
            </Panel>
          ) : error ? (
            <Panel
              className="mt-14 flex min-h-96 flex-col items-center justify-center text-center"
              padding="lg"
              variant="raised"
            >
              <CircleAlert
                className="text-danger"
                size={36}
              />

              <h2 className="mt-5 font-display text-2xl font-semibold text-white">
                Dashboard unavailable
              </h2>

              <p className="mt-3 max-w-lg leading-7 text-copy-muted">
                {error}
              </p>
            </Panel>
          ) : !hasCompletedAnalyses ? (
            <div className="mt-14 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
              <Panel
                className="flex min-h-[30rem] flex-col items-center justify-center text-center"
                padding="lg"
                variant="raised"
              >
                <div className="flex size-16 items-center justify-center rounded-3xl border border-lime-soft/20 bg-lime-soft/10 text-lime-soft">
                  <FileVideo2 size={30} />
                </div>

                <p className="mt-7 text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                  Your first analysis
                </p>

                <h2 className="mt-3 max-w-xl font-display text-4xl font-semibold tracking-[-0.045em] text-white">
                  Start building your swing profile.
                </h2>

                <p className="mt-5 max-w-xl leading-7 text-copy-muted">
                  Upload one swing video and TempoAI
                  will measure your mechanics,
                  generate coaching feedback, and save
                  the result to your private history.
                </p>

                <Button
                  className="mt-8"
                  size="lg"
                  to="/analysis/new"
                >
                  Analyze your first swing
                  <ArrowRight size={18} />
                </Button>
              </Panel>

              <Panel
                padding="lg"
                variant="muted"
              >
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                  What you will unlock
                </p>

                <div className="mt-7 space-y-5">
                  {[
                    {
                      icon: Gauge,
                      title:
                        "Swing score and metrics",
                      description:
                        "Review posture, tempo, rotation, balance, and other measured areas.",
                    },
                    {
                      icon: Clock3,
                      title:
                        "Progress over time",
                      description:
                        "Build a private history and compare completed analyses.",
                    },
                    {
                      icon: Target,
                      title:
                        "Focused coaching",
                      description:
                        "Receive findings, priorities, and drills based on your uploaded swing.",
                    },
                    {
                      icon: Sparkles,
                      title:
                        "Personalized dashboard",
                      description:
                        "Your latest score, averages, recent swings, and coaching focus will appear here.",
                    },
                  ].map(
                    ({
                      icon: Icon,
                      title,
                      description,
                    }) => (
                      <div
                        key={title}
                        className="flex items-start gap-4"
                      >
                        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                          <Icon size={20} />
                        </div>

                        <div>
                          <p className="font-semibold text-white">
                            {title}
                          </p>

                          <p className="mt-1 text-sm leading-6 text-copy-muted">
                            {description}
                          </p>
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </Panel>
            </div>
          ) : (
            <>
              <div className="mt-14 grid gap-6 xl:grid-cols-[0.95fr_1.45fr]">
                <Panel
                  className="flex min-h-[28rem] items-center justify-center"
                  padding="lg"
                  variant="raised"
                >
                  <ScoreRing
                    label="Latest swing score"
                    score={latestScore}
                    subtitle="Most recent completed analysis"
                  />
                </Panel>

                <div className="grid gap-6 sm:grid-cols-2">
                  <MetricCard
                    icon={
                      <Activity
                        className="text-lime-soft"
                        size={22}
                      />
                    }
                    title="Swings analyzed"
                    trend="Completed analyses"
                    value={completedAnalyses.length.toString()}
                  />

                  <MetricCard
                    icon={
                      <Clock3
                        className="text-ice"
                        size={22}
                      />
                    }
                    title="Average tempo"
                    trend={
                      averageTempo === null
                        ? "Not measured yet"
                        : "Across completed swings"
                    }
                    value={
                      averageTempo === null
                        ? "—"
                        : `${averageTempo.toFixed(
                            2,
                          )}:1`
                    }
                  />

                  <MetricCard
                    icon={
                      <Gauge
                        className="text-lime-soft"
                        size={22}
                      />
                    }
                    title="Latest score"
                    trend="Most recent result"
                    value={latestScore.toString()}
                  />

                  <MetricCard
                    icon={
                      <Target
                        className="text-ice"
                        size={22}
                      />
                    }
                    title="Average consistency"
                    trend={
                      averageConsistency === null
                        ? "Not measured yet"
                        : "Across completed swings"
                    }
                    value={
                      averageConsistency === null
                        ? "—"
                        : `${Math.round(
                            averageConsistency,
                          )}%`
                    }
                  />
                </div>
              </div>

              <div className="mt-16 grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
                <Panel
                  padding="none"
                  variant="raised"
                >
                  <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-display text-2xl font-semibold text-white">
                        Recent swings
                      </p>

                      <p className="mt-1 text-sm text-copy-muted">
                        Your latest completed swing analyses.
                      </p>
                    </div>

                    <Link
                      className="inline-flex items-center gap-2 text-sm font-semibold text-lime-soft transition hover:text-lime-bright"
                      to="/history"
                    >
                      View all
                      <ArrowRight size={16} />
                    </Link>
                  </div>

                  <div className="divide-y divide-white/10">
                    {recentAnalyses.map(
                      (analysis) => (
                        <Link
                          key={analysis.id}
                          className="group grid gap-5 px-6 py-6 transition hover:bg-white/[0.025] md:grid-cols-[auto_1fr_auto] md:items-center"
                          to={`/analysis/${analysis.id}`}
                        >
                          <div className="relative flex aspect-video w-full items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-[radial-gradient(circle_at_center,_#173222_0%,_#0a130f_70%)] md:w-40">
                            <div className="absolute h-[60%] w-[2px] rotate-[-10deg] bg-lime-soft shadow-[0_0_14px_rgba(132,255,77,0.55)]" />

                            <div className="flex size-10 items-center justify-center rounded-full border border-white/10 bg-black/35 text-white backdrop-blur">
                              <Play
                                fill="currentColor"
                                size={16}
                              />
                            </div>
                          </div>

                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-3">
                              <h2 className="truncate font-display text-lg font-semibold text-white transition group-hover:text-lime-soft">
                                {formatFilename(
                                  analysis.originalFilename,
                                )}
                              </h2>

                              <Badge variant="success">
                                Complete
                              </Badge>
                            </div>

                            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-copy-subtle">
                              <span className="inline-flex items-center gap-1.5">
                                <CalendarDays
                                  size={14}
                                />

                                {formatDate(
                                  analysis.createdAt,
                                )}
                              </span>

                              {analysis.tempoRatio !==
                                null && (
                                <span>
                                  Tempo{" "}
                                  {analysis.tempoRatio.toFixed(
                                    2,
                                  )}
                                  :1
                                </span>
                              )}
                            </div>

                            <p className="mt-4 line-clamp-2 text-sm text-copy-muted">
                              {analysis.primaryFinding ??
                                "Open this analysis to review your measured swing results."}
                            </p>
                          </div>

                          <div className="flex items-center justify-between gap-5 md:flex-col md:items-end">
                            <div className="text-right">
                              <p className="font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                                {analysis.swingScore ??
                                  "—"}
                              </p>

                              <p className="mt-1 text-xs uppercase tracking-[0.18em] text-copy-subtle">
                                Score
                              </p>
                            </div>

                            <ArrowRight
                              className="text-copy-subtle transition group-hover:translate-x-1 group-hover:text-lime-soft"
                              size={20}
                            />
                          </div>
                        </Link>
                      ),
                    )}
                  </div>
                </Panel>

                <div className="grid gap-6">
                  <Panel
                    padding="lg"
                    variant="raised"
                  >
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      Current focus
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                      {latestAnalysis?.primaryFinding ??
                        "Review your latest analysis."}
                    </h2>

                    <p className="mt-5 leading-7 text-copy-muted">
                      This focus comes from your most
                      recently completed swing analysis.
                    </p>

                    {latestAnalysis?.recommendation && (
                      <div className="mt-7 border-t border-white/10 pt-6">
                        <p className="text-sm font-semibold text-white">
                          Recommended next step
                        </p>

                        <p className="mt-2 text-sm leading-6 text-copy-muted">
                          {
                            latestAnalysis.recommendation
                          }
                        </p>
                      </div>
                    )}
                  </Panel>

                  <Panel
                    padding="lg"
                    variant="muted"
                  >
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-copy-subtle">
                      Next session
                    </p>

                    <h2 className="mt-3 font-display text-2xl font-semibold text-white">
                      Record another comparable swing.
                    </h2>

                    <p className="mt-4 leading-7 text-copy-muted">
                      Use a similar camera position and
                      framing to make your results easier
                      to compare.
                    </p>

                    <Button
                      className="mt-7 w-full"
                      to="/analysis/new"
                      variant="secondary"
                    >
                      Start session
                    </Button>
                  </Panel>
                </div>
              </div>
            </>
          )}
        </Container>
      </Section>
    </main>
  );
}

export default DashboardPage;