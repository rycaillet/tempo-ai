import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Dumbbell,
  Gauge,
  ScanLine,
  Sparkles,
  Target,
} from "lucide-react";
import { Link } from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import ScoreRing from "../components/ui/ScoreRing";
import Section from "../components/ui/Section";

const demoMetrics = [
  {
    label: "Tempo",
    score: 86,
    result: "3.1:1",
    description:
      "The backswing and downswing maintain a controlled, repeatable rhythm.",
  },
  {
    label: "Address posture",
    score: 78,
    result: "Good",
    description:
      "The setup is athletic, with a small opportunity to improve hip hinge.",
  },
  {
    label: "Rotation",
    score: 82,
    result: "Good",
    description:
      "Shoulder and hip rotation remain coordinated through most of the swing.",
  },
  {
    label: "Head stability",
    score: 88,
    result: "Strong",
    description:
      "Head movement remains controlled throughout the backswing and impact.",
  },
  {
    label: "Early extension",
    score: 91,
    result: "Excellent",
    description:
      "Hip depth is preserved well while moving through the downswing.",
  },
];

const practiceSteps = [
  {
    title: "Warm up",
    duration: "5 minutes",
    description:
      "Begin with relaxed half-speed swings to establish balance and rhythm.",
  },
  {
    title: "Address posture drill",
    duration: "10 minutes",
    description:
      "Build a balanced setup with consistent hip hinge, knee flex, and hand position.",
  },
  {
    title: "Controlled swings",
    duration: "10 minutes",
    description:
      "Record five comparable 7-iron swings from the same camera position.",
  },
];

function DemoSwingVisual() {
  return (
    <div className="relative overflow-hidden bg-black">
      <img
        alt="TempoAI address-position demonstration showing golfer posture, pose landmarks, club position, ball position, and setup measurements"
        className="block h-auto w-full"
        loading="eager"
        src="/tempo-ai-demo-address-visual.png"
      />

      <div className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-white/5" />
    </div>
  );
}

function DemoPage() {
  return (
    <main className="min-h-screen bg-canvas text-copy">
      <nav className="border-b border-white/10 bg-canvas/90 py-5 backdrop-blur-xl">
        <Container className="flex items-center justify-between gap-4">
          <Link
            className="font-display text-xl font-semibold tracking-[-0.04em] text-white"
            to="/"
          >
            Tempo
            <span className="text-lime-soft">
              AI
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              className="hidden text-sm font-semibold text-copy-muted transition hover:text-white sm:block"
              to="/login"
            >
              Log in
            </Link>

            <Button
              size="sm"
              to="/register"
            >
              Create account
            </Button>
          </div>
        </Container>
      </nav>

      <Section spacing="lg">
        <Container size="wide">
          <Link
            className="inline-flex items-center gap-2 text-sm font-semibold text-copy-muted transition hover:text-white"
            to="/"
          >
            <ArrowLeft size={17} />
            Return home
          </Link>

          <div className="mt-10 flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
                  Public product demo
                </p>

                <Badge variant="info">
                  Sample analysis
                </Badge>
              </div>

              <h1 className="mt-4 font-display text-5xl font-semibold tracking-[-0.05em] text-white">
                7-Iron Swing Demonstration
              </h1>

              <p className="mt-5 max-w-3xl text-lg leading-8 text-copy-muted">
                Explore a representative TempoAI report showing how swing
                measurements are transformed into focused coaching feedback
                and a practical improvement plan.
              </p>
            </div>

            <Button
              size="lg"
              to="/register"
            >
              Analyze your own swing
              <ArrowRight size={18} />
            </Button>
          </div>

          <div className="mt-14 grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.65fr)]">
            <Panel
              className="overflow-hidden"
              padding="none"
              variant="raised"
            >
              <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-display text-xl font-semibold text-white">
                    Visual swing analysis
                  </p>

                  <p className="mt-1 text-sm text-copy-subtle">
                    Address position selected
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <Badge variant="neutral">
                    Read-only demo
                  </Badge>

                  <Badge variant="success">
                    Analysis complete
                  </Badge>
                </div>
              </div>

              <DemoSwingVisual />

              <div className="flex items-start gap-3 border-t border-white/10 px-6 py-5">
                <ScanLine
                  className="mt-0.5 shrink-0 text-ice"
                  size={18}
                />

                <p className="text-sm leading-6 text-copy-muted">
                  TempoAI identifies body landmarks, setup posture, club
                  position, and ball alignment from the golfer&apos;s uploaded
                  recording. The live report also includes selectable swing
                  phases and detailed metric explanations.
                </p>
              </div>
            </Panel>

            <div className="grid gap-6">
              <Panel
                className="flex flex-col items-center justify-center"
                padding="lg"
                variant="raised"
              >
                <ScoreRing
                  label="Swing score"
                  rating="Good"
                  score={84}
                  subtitle="Representative demo result"
                />
              </Panel>

              <Panel
                padding="lg"
                variant="raised"
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                    <Sparkles size={21} />
                  </div>

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                      TempoAI Coach
                    </p>

                    <h2 className="mt-1 font-display text-xl font-semibold text-white">
                      Build a balanced address position
                    </h2>
                  </div>
                </div>

                <p className="mt-5 text-sm leading-7 text-copy-muted">
                  The sample setup demonstrates a stable stance, measured hip
                  hinge, and neutral hand position. The primary opportunity is
                  maintaining this posture consistently as the backswing
                  begins.
                </p>
              </Panel>
            </div>
          </div>

          <section className="mt-16">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                Measured performance
              </p>

              <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                Swing metric overview
              </h2>

              <p className="mt-3 max-w-3xl leading-7 text-copy-muted">
                Each completed analysis presents individual scores,
                classifications, measurement explanations, and
                confidence-aware coaching observations.
              </p>
            </div>

            <div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-5">
              {demoMetrics.map((metric) => (
                <Panel
                  key={metric.label}
                  className="h-full"
                  padding="md"
                  variant="raised"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold uppercase tracking-[0.16em] text-copy-subtle">
                      {metric.label}
                    </p>

                    <Gauge
                      className="shrink-0 text-lime-soft"
                      size={18}
                    />
                  </div>

                  <p className="mt-5 font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                    {metric.score}
                  </p>

                  <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/8">
                    <div
                      className="h-full rounded-full bg-lime-soft"
                      style={{
                        width: `${metric.score}%`,
                      }}
                    />
                  </div>

                  <p className="mt-4 text-sm font-semibold text-ice">
                    {metric.result}
                  </p>

                  <p className="mt-3 text-sm leading-6 text-copy-muted">
                    {metric.description}
                  </p>
                </Panel>
              ))}
            </div>
          </section>

          <div className="mt-16 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="grid gap-6">
              <Panel
                padding="lg"
                variant="raised"
              >
                <div className="flex items-start gap-4">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                    <CheckCircle2 size={23} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      AI coaching summary
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                      A balanced setup with a clear next priority
                    </h2>

                    <p className="mt-5 leading-8 text-copy-muted">
                      This sample demonstrates a stable address position with
                      athletic posture, measured hip hinge, and neutral hand
                      placement. Repeating the same setup consistently can
                      create a stronger foundation for tempo, rotation, and
                      contact.
                    </p>
                  </div>
                </div>
              </Panel>

              <Panel
                padding="lg"
                variant="raised"
              >
                <div className="flex items-start gap-4">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-lime-soft/10 font-display text-lg font-semibold text-lime-soft">
                    1
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="font-display text-2xl font-semibold text-white">
                        Repeat the same address posture
                      </h2>

                      <Badge variant="warning">
                        High priority
                      </Badge>
                    </div>

                    <p className="mt-2 text-sm font-medium text-ice">
                      Address phase
                    </p>

                    <p className="mt-5 leading-7 text-copy-muted">
                      Begin from a balanced position over the middle of the feet.
                      Maintain consistent spine tilt, hip hinge, knee flex, and
                      hand position before beginning the takeaway.
                    </p>

                    <div className="mt-6 border-t border-white/10 pt-6">
                      <p className="font-semibold text-white">
                        Recommended drill
                      </p>

                      <p className="mt-2 text-sm leading-6 text-copy-muted">
                        Place an alignment stick on the ground and rehearse five
                        identical setups before hitting each ball. Check stance
                        width, ball position, and distance from the ball each
                        time.
                      </p>
                    </div>
                  </div>
                </div>
              </Panel>
            </div>

            <Panel
              className="h-fit"
              padding="lg"
              variant="raised"
            >
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

              <div className="mt-8 space-y-7">
                {practiceSteps.map((step, index) => (
                  <div
                    key={step.title}
                    className="grid grid-cols-[auto_1fr] gap-4"
                  >
                    <div className="flex size-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-semibold text-white">
                      {index + 1}
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-semibold text-white">
                          {step.title}
                        </p>

                        <span className="inline-flex items-center gap-1.5 text-xs text-copy-subtle">
                          <Clock3 size={13} />
                          {step.duration}
                        </span>
                      </div>

                      <p className="mt-2 text-sm leading-6 text-copy-muted">
                        {step.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <Button
                className="mt-8 w-full"
                to="/register"
              >
                Create your account
                <Target size={17} />
              </Button>
            </Panel>
          </div>

          <Panel
            className="mt-16 text-center"
            padding="lg"
            variant="muted"
          >
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
              Ready to analyze your swing?
            </p>

            <h2 className="mx-auto mt-4 max-w-2xl font-display text-3xl font-semibold tracking-[-0.04em] text-white">
              Create a private account and receive feedback generated from your
              own uploaded video.
            </h2>

            <p className="mx-auto mt-4 max-w-2xl leading-7 text-copy-muted">
              The public demo uses representative sample information. Your
              account analyses are private and tied only to your authenticated
              session.
            </p>

            <Button
              className="mt-7"
              size="lg"
              to="/register"
            >
              Get started
              <ArrowRight size={18} />
            </Button>
          </Panel>
        </Container>
      </Section>
    </main>
  );
}

export default DemoPage;