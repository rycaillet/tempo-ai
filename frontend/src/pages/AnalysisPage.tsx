import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Dumbbell,
  Gauge,
  Play,
  RotateCcw,
  Sparkles,
  Target,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AnalysisSkeleton from "../components/analysis/AnalysisSkeleton";
import PhaseCoachPanel from "../components/analysis/PhaseCoachPanel";
import SwingPoseOverlay from "../components/analysis/SwingPoseOverlay";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import ScoreRing from "../components/ui/ScoreRing";
import Section from "../components/ui/Section";
import { getAnalysis } from "../services/analysisService";
import type { SwingAnalysis } from "../types/analysis";

const severityVariant = {
  High: "warning",
  Medium: "info",
  Low: "neutral",
} as const;

function AnalysisPage() {
  const { swingId } = useParams();

  const [analysis, setAnalysis] = useState<SwingAnalysis | null>(null);
  const [selectedPhaseId, setSelectedPhaseId] = useState("impact");

  useEffect(() => {
    async function loadAnalysis() {
      const result = await getAnalysis(swingId ?? "demo-swing");

      setAnalysis(result);
    }

    void loadAnalysis();
  }, [swingId]);

  if (!analysis) {
    return <AnalysisSkeleton />;
  }

  const {
    summary: analysisSummary,
    phases: swingPhases,
    metrics: swingMetrics,
    findings: swingFindings,
    practicePlan,
  } = analysis;

  const selectedPhase =
    swingPhases.find((phase) => phase.id === selectedPhaseId) ??
    swingPhases[0];

  const selectedFinding = selectedPhase.coaching.findingId
    ? swingFindings.find(
        (finding) => finding.id === selectedPhase.coaching.findingId,
      )
    : undefined;

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="wide">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-sm font-semibold text-copy-muted transition hover:text-white"
          >
            <ArrowLeft size={17} />
            Return to dashboard
          </Link>

          <div className="mt-10 flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
                Swing analysis
              </p>

              <h1 className="mt-4 font-display text-5xl font-semibold tracking-[-0.05em] text-white">
                {analysisSummary.title}
              </h1>

              <div className="mt-5 flex flex-wrap gap-x-6 gap-y-3 text-sm text-copy-muted">
                <span>{analysisSummary.club}</span>

                <span>{analysisSummary.cameraAngle}</span>

                <span className="inline-flex items-center gap-2">
                  <CalendarDays size={15} />
                  {analysisSummary.date}
                </span>

                <span className="text-copy-subtle">
                  Analysis ID: {swingId ?? analysisSummary.id}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button to="/analysis/new" variant="secondary">
                <RotateCcw size={17} />
                Analyze another
              </Button>

              <Button to="/compare">
                Compare swing
                <ChevronRight size={17} />
              </Button>
            </div>
          </div>

          <div className="mt-14 grid gap-6 xl:grid-cols-[1.55fr_0.65fr]">
            <Panel padding="none" variant="raised">
              <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
                <div>
                  <p className="font-display text-xl font-semibold text-white">
                    Down-the-line video
                  </p>

                  <p className="mt-1 text-sm text-copy-subtle">
                    {selectedPhase.label} position selected ·{" "}
                    {selectedPhase.timestamp}
                  </p>
                </div>

                <Badge variant="success">Analysis complete</Badge>
              </div>

              <div className="relative aspect-video overflow-hidden bg-[radial-gradient(circle_at_center,_#173222_0%,_#0a130f_62%,_#050a07_100%)]">
                <div className="absolute inset-8 rounded-panel border border-white/8 bg-black/10" />

                <SwingPoseOverlay
                  variant={selectedPhase.coaching.poseVariant}
                />

                <PhaseCoachPanel
                  phase={selectedPhase}
                  finding={selectedFinding}
                />

                <button
                  aria-label="Play analyzed swing"
                  className="absolute left-1/2 top-1/2 z-10 flex size-20 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-black/45 text-white backdrop-blur transition hover:scale-105 hover:bg-black/60"
                  type="button"
                >
                  <Play fill="currentColor" size={28} />
                </button>

                <div className="absolute bottom-5 left-5 right-5 z-10 rounded-2xl border border-white/10 bg-black/45 p-4 backdrop-blur">
                  <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
                    {swingPhases.map((phase) => {
                      const isSelected = phase.id === selectedPhase.id;

                      return (
                        <button
                          key={phase.id}
                          aria-label={`View ${phase.label} phase`}
                          aria-pressed={isSelected}
                          className="group flex flex-col items-center gap-2 text-center"
                          type="button"
                          onClick={() => setSelectedPhaseId(phase.id)}
                        >
                          <span
                            className={[
                              "size-2.5 rounded-full transition",
                              isSelected
                                ? "scale-125 bg-lime-soft shadow-[0_0_12px_rgba(132,255,77,0.7)]"
                                : "bg-copy-subtle group-hover:bg-white",
                            ].join(" ")}
                          />

                          <span
                            className={[
                              "text-[10px] font-semibold uppercase tracking-[0.16em] transition",
                              isSelected
                                ? "text-lime-soft"
                                : "text-copy-subtle group-hover:text-white",
                            ].join(" ")}
                          >
                            {phase.label}
                          </span>

                          <span
                            className={[
                              "text-[10px] transition",
                              isSelected
                                ? "text-white"
                                : "text-copy-subtle",
                            ].join(" ")}
                          >
                            {phase.timestamp}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </Panel>

            <Panel
              className="flex flex-col items-center justify-center"
              padding="lg"
              variant="raised"
            >
              <ScoreRing
                label="Swing score"
                score={analysisSummary.overallScore}
                subtitle={analysisSummary.change}
              />
            </Panel>
          </div>

          <div className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
            {swingMetrics.map((metric) => (
              <Panel key={metric.id} padding="md" variant="raised">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                    {metric.label}
                  </p>

                  <Gauge className="text-lime-soft" size={18} />
                </div>

                <p className="mt-5 font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                  {metric.score}
                </p>

                <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/8">
                  <div
                    className="h-full rounded-full bg-lime-soft"
                    style={{ width: `${metric.score}%` }}
                  />
                </div>

                <p className="mt-4 text-sm leading-6 text-copy-muted">
                  {metric.description}
                </p>
              </Panel>
            ))}
          </div>

          <div className="mt-16 grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
            <div className="space-y-6">
              <Panel padding="lg" variant="raised">
                <div className="flex items-start gap-4">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                    <Sparkles size={23} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      AI coaching summary
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                      A stronger, more controlled swing.
                    </h2>

                    <p className="mt-5 leading-8 text-copy-muted">
                      {analysisSummary.summary}
                    </p>

                    <div className="mt-7 flex items-start gap-3 rounded-2xl border border-lime-soft/15 bg-lime-soft/[0.05] p-4">
                      <CheckCircle2
                        className="mt-0.5 shrink-0 text-lime-soft"
                        size={20}
                      />

                      <div>
                        <p className="font-semibold text-white">
                          Strongest improvement
                        </p>

                        <p className="mt-1 text-sm leading-6 text-copy-muted">
                          {analysisSummary.strength}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </Panel>

              <div>
                <div className="mb-6 flex items-end justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      Coaching priorities
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold text-white">
                      What to work on next
                    </h2>
                  </div>

                  <p className="hidden text-sm text-copy-subtle sm:block">
                    Prioritized by impact
                  </p>
                </div>

                <div className="space-y-4">
                  {swingFindings.map((finding) => {
                    const isSelectedFinding =
                      selectedFinding?.id === finding.id;

                    return (
                      <Panel
                        key={finding.id}
                        className={[
                          "transition",
                          isSelectedFinding
                            ? "ring-1 ring-lime-soft/50"
                            : "",
                        ].join(" ")}
                        padding="lg"
                        variant="raised"
                      >
                        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
                          <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-lime-soft/10 font-display text-lg font-semibold text-lime-soft">
                            {finding.priority}
                          </div>

                          <div className="flex-1">
                            <div className="flex flex-wrap items-center gap-3">
                              <h3 className="font-display text-2xl font-semibold text-white">
                                {finding.title}
                              </h3>

                              <Badge
                                variant={
                                  severityVariant[finding.severity]
                                }
                              >
                                {finding.severity} priority
                              </Badge>

                              {isSelectedFinding && (
                                <Badge variant="success">
                                  Selected phase
                                </Badge>
                              )}
                            </div>

                            <p className="mt-2 text-sm font-medium text-ice">
                              {finding.phase} phase
                            </p>

                            <p className="mt-5 leading-7 text-copy-muted">
                              {finding.explanation}
                            </p>

                            <div className="mt-6 grid gap-5 border-t border-white/10 pt-6 md:grid-cols-2">
                              <div>
                                <p className="text-sm font-semibold text-white">
                                  Supporting evidence
                                </p>

                                <p className="mt-2 text-sm leading-6 text-copy-muted">
                                  {finding.evidence}
                                </p>
                              </div>

                              <div>
                                <p className="text-sm font-semibold text-white">
                                  {finding.drill.name}
                                </p>

                                <p className="mt-2 text-sm leading-6 text-copy-muted">
                                  {finding.drill.instructions}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Panel>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <Panel padding="lg" variant="raised">
                <div className="flex items-center gap-3">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-ice/10 text-ice">
                    <Dumbbell size={21} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                      Practice plan
                    </p>

                    <h2 className="mt-1 font-display text-2xl font-semibold text-white">
                      Your next 25 minutes
                    </h2>
                  </div>
                </div>

                <div className="mt-8 space-y-6">
                  {practicePlan.map((item, index) => (
                    <div
                      key={item.label}
                      className="grid grid-cols-[auto_1fr] gap-4"
                    >
                      <div className="flex size-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-semibold text-white">
                        {index + 1}
                      </div>

                      <div>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="font-semibold text-white">
                            {item.label}
                          </p>

                          <span className="inline-flex items-center gap-1.5 text-xs text-copy-subtle">
                            <Clock3 size={13} />
                            {item.duration}
                          </span>
                        </div>

                        <p className="mt-2 text-sm leading-6 text-copy-muted">
                          {item.instructions}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <Button className="mt-8 w-full" to="/analysis/new">
                  Record next swing
                  <Target size={17} />
                </Button>
              </Panel>

              <Panel padding="lg" variant="muted">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                  Analysis limitations
                </p>

                <p className="mt-4 text-sm leading-7 text-copy-muted">
                  Results depend on camera placement, lighting, video
                  quality, pose-detection confidence, and the visibility of
                  your full body throughout the recording.
                </p>
              </Panel>
            </div>
          </div>
        </Container>
      </Section>
    </main>
  );
}

export default AnalysisPage;