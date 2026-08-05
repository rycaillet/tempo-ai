import {
  ArrowRight,
  Play,
} from "lucide-react";
import { Link } from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import Section from "../components/ui/Section";

function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-canvas text-copy">
      <div className="pointer-events-none absolute left-1/2 top-[-20rem] h-[40rem] w-[40rem] -translate-x-1/2 rounded-full bg-lime-soft/10 blur-[140px]" />

      <nav className="relative z-10 py-6">
        <Container className="flex items-center justify-between">
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
              className="rounded-full px-4 py-2 text-sm font-medium text-slate-300 transition hover:text-white"
              to="/login"
            >
              Log in
            </Link>

            <Button
              size="sm"
              to="/register"
            >
              Get started
            </Button>
          </div>
        </Container>
      </nav>

      <Section
        className="relative z-10 min-h-[calc(100vh-96px)]"
        spacing="md"
      >
        <Container className="grid min-h-[calc(100vh-224px)] items-center gap-16 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
              AI-powered swing intelligence
            </p>

            <h1 className="mt-6 max-w-3xl font-display text-5xl font-semibold leading-[0.98] tracking-[-0.055em] text-white sm:text-6xl lg:text-7xl">
              Every swing tells a story.

              <span className="mt-2 block text-copy-muted">
                Understand yours.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-lg leading-8 text-copy-muted">
              TempoAI transforms recorded golf swings
              into visual movement data, focused
              coaching feedback, and practical drills.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Button
                size="lg"
                to="/register"
              >
                Analyze your swing
                <ArrowRight
                  size={18}
                  strokeWidth={2.4}
                />
              </Button>

              <Button
                size="lg"
                to="/demo"
                variant="secondary"
              >
                <Play size={17} />
                View product demo
              </Button>
            </div>

            <p className="mt-4 text-sm text-copy-subtle">
              A free account is required to upload and
              privately save swing analyses.
            </p>
          </div>

          <div className="relative">
            <Panel
              className="overflow-hidden rounded-[2rem]"
              padding="none"
              variant="raised"
            >
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-white">
                    Address-position analysis
                  </p>

                  <p className="mt-1 text-xs text-copy-subtle">
                    7 Iron · Demo result
                  </p>
                </div>

                <Badge variant="success">
                  Analysis complete
                </Badge>
              </div>

              <Link
                aria-label="Open the public TempoAI product demonstration"
                className="group relative block overflow-hidden bg-black"
                to="/demo"
              >
                <img
                  alt="TempoAI demonstration showing a golfer at address with posture, club, ball, and body-tracking measurements"
                  className="block h-auto w-full transition duration-500 group-hover:scale-[1.015]"
                  loading="eager"
                  src="/tempo-ai-demo-address-visual.png"
                />

                <div className="pointer-events-none absolute inset-0 ring-1 ring-inset ring-white/5" />

                <div className="absolute inset-x-5 bottom-5 flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-black/65 px-4 py-3 backdrop-blur">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                      Selected phase
                    </p>

                    <p className="mt-1 text-sm font-semibold text-lime-soft">
                      Address
                    </p>
                  </div>

                  <span className="inline-flex items-center gap-2 text-sm font-semibold text-white">
                    Explore analysis
                    <ArrowRight
                      className="transition group-hover:translate-x-1"
                      size={16}
                    />
                  </span>
                </div>
              </Link>
            </Panel>

            <Panel
              className="absolute -bottom-8 -right-4 rounded-3xl backdrop-blur sm:right-6"
              padding="sm"
              variant="raised"
            >
              <p className="text-xs uppercase tracking-[0.2em] text-copy-subtle">
                Demo swing score
              </p>

              <p className="mt-2 font-display text-5xl font-semibold tracking-[-0.06em] text-white">
                84
              </p>

              <p className="mt-1 text-sm text-lime-soft">
                Good
              </p>
            </Panel>
          </div>
        </Container>
      </Section>
    </main>
  );
}

export default LandingPage;