import {
  Activity,
  ArrowRight,
  CalendarDays,
  Clock3,
  Gauge,
  Play,
  Target,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import MetricCard from "../components/ui/MetricCard";
import PageHeader from "../components/ui/PageHeader";
import Panel from "../components/ui/Panel";
import ScoreRing from "../components/ui/ScoreRing";
import Section from "../components/ui/Section";
import { dashboardMetrics, recentSwings } from "../data/dashboard";

function DashboardPage() {
  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="wide">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <PageHeader
              eyebrow="Performance overview"
              title="Welcome back, Ryan."
              description="Review your latest swing data, track improvement, and continue building a more repeatable golf swing."
            />

            <Button to="/analysis/new" size="lg">
              Analyze a new swing
              <ArrowRight size={18} />
            </Button>
          </div>

          <div className="mt-14 grid gap-6 xl:grid-cols-[0.95fr_1.45fr]">
            <Panel
              className="flex min-h-[28rem] items-center justify-center"
              padding="lg"
              variant="raised"
            >
              <ScoreRing
                label="Swing score"
                score={dashboardMetrics.overallScore}
                subtitle={dashboardMetrics.scoreChange}
              />
            </Panel>

            <div className="grid gap-6 sm:grid-cols-2">
              <MetricCard
                title="Swings analyzed"
                value={dashboardMetrics.totalSwings}
                trend="+3 this month"
                icon={<Activity className="text-lime-soft" size={22} />}
              />

              <MetricCard
                title="Average tempo"
                value={dashboardMetrics.averageTempo}
                trend="Inside target range"
                icon={<Clock3 className="text-ice" size={22} />}
              />

              <MetricCard
                title="Most improved club"
                value={dashboardMetrics.bestClub}
                trend="+9 average score"
                icon={<Target className="text-lime-soft" size={22} />}
              />

              <MetricCard
                title="Swing consistency"
                value={dashboardMetrics.consistency}
                trend="+4% over 30 days"
                icon={<Gauge className="text-ice" size={22} />}
              />
            </div>
          </div>

          <div className="mt-16 grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
            <Panel padding="none" variant="raised">
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
                  to="/history"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-lime-soft transition hover:text-lime-bright"
                >
                  View all
                  <ArrowRight size={16} />
                </Link>
              </div>

              <div className="divide-y divide-white/10">
                {recentSwings.map((swing) => (
                  <Link
                    key={swing.id}
                    to={`/analysis/${swing.id}`}
                    className="group grid gap-5 px-6 py-6 transition hover:bg-white/[0.025] md:grid-cols-[auto_1fr_auto] md:items-center"
                  >
                    <div className="relative flex aspect-video w-full items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-[radial-gradient(circle_at_center,_#173222_0%,_#0a130f_70%)] md:w-40">
                      <div className="absolute h-[60%] w-[2px] rotate-[-10deg] bg-lime-soft shadow-[0_0_14px_rgba(132,255,77,0.55)]" />

                      <div className="flex size-10 items-center justify-center rounded-full border border-white/10 bg-black/35 text-white backdrop-blur">
                        <Play size={16} fill="currentColor" />
                      </div>
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h2 className="font-display text-lg font-semibold text-white transition group-hover:text-lime-soft">
                          {swing.title}
                        </h2>

                        <Badge
                          variant={
                            swing.status === "Complete"
                              ? "success"
                              : "warning"
                          }
                        >
                          {swing.status}
                        </Badge>
                      </div>

                      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-copy-subtle">
                        <span>{swing.club}</span>
                        <span>{swing.cameraAngle}</span>

                        <span className="inline-flex items-center gap-1.5">
                          <CalendarDays size={14} />
                          {swing.date}
                        </span>
                      </div>

                      <p className="mt-4 text-sm text-copy-muted">
                        {swing.finding}
                      </p>
                    </div>

                    <div className="flex items-center justify-between gap-5 md:flex-col md:items-end">
                      <div className="text-right">
                        <p className="font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                          {swing.score}
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
                ))}
              </div>
            </Panel>

            <div className="grid gap-6">
              <Panel padding="lg" variant="raised">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      Current focus
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                      Maintain posture through impact.
                    </h2>
                  </div>

                  <div className="hidden rounded-2xl bg-lime-soft/10 p-3 text-lime-soft sm:block">
                    <TrendingUp size={24} />
                  </div>
                </div>

                <p className="mt-5 leading-7 text-copy-muted">
                  Your most recent swings show improved rotation, but your hip
                  depth still decreases slightly during the downswing.
                </p>

                <div className="mt-7 border-t border-white/10 pt-6">
                  <p className="text-sm font-semibold text-white">
                    Recommended drill
                  </p>

                  <p className="mt-2 text-sm leading-6 text-copy-muted">
                    Practice slow-motion wall touches to maintain hip depth
                    through the impact position.
                  </p>
                </div>
              </Panel>

              <Panel padding="lg" variant="muted">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-copy-subtle">
                  Next session
                </p>

                <h2 className="mt-3 font-display text-2xl font-semibold text-white">
                  Record five controlled 7-iron swings.
                </h2>

                <p className="mt-4 leading-7 text-copy-muted">
                  Use the same down-the-line camera position so TempoAI can
                  compare posture and tempo accurately.
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
        </Container>
      </Section>
    </main>
  );
}

export default DashboardPage;