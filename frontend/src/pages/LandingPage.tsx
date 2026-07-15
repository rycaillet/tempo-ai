import { ArrowRight, Play } from "lucide-react";
import { Link } from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import Section from "../components/ui/Section";

const swingPhases = ["Address", "Top", "Impact", "Finish"];

function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-canvas text-copy">
      <div className="pointer-events-none absolute left-1/2 top-[-20rem] h-[40rem] w-[40rem] -translate-x-1/2 rounded-full bg-lime-soft/10 blur-[140px]" />

      <nav className="relative z-10 py-6">
        <Container className="flex items-center justify-between">
          <Link
            to="/"
            className="font-display text-xl font-semibold tracking-[-0.04em] text-white"
          >
            Tempo<span className="text-lime-soft">AI</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-full px-4 py-2 text-sm font-medium text-slate-300 transition hover:text-white"
            >
              Log in
            </Link>

            <Button to="/register" size="sm">
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
              TempoAI transforms recorded golf swings into visual movement data,
              focused coaching feedback, and practical drills.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Button to="/register" size="lg">
                Analyze a swing
                <ArrowRight size={18} strokeWidth={2.4} />
              </Button>

              <Button to="/dashboard" size="lg" variant="secondary">
                <Play size={17} />
                View demo
              </Button>
            </div>
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
                    Down-the-line analysis
                  </p>

                  <p className="mt-1 text-xs text-copy-subtle">
                    7 Iron · July 15
                  </p>
                </div>

                <Badge variant="success">Analysis complete</Badge>
              </div>

              <div className="relative aspect-[4/3] bg-[radial-gradient(circle_at_center,_#173222_0%,_#0a130f_62%,_#060c09_100%)]">
                <div className="absolute inset-x-10 bottom-10 top-10 rounded-[1.75rem] border border-white/10 bg-white/[0.025]" />

                <div className="absolute left-1/2 top-1/2 h-[66%] w-[2px] -translate-x-1/2 -translate-y-1/2 rotate-[-8deg] bg-lime-soft shadow-[0_0_20px_rgba(132,255,77,0.7)]" />

                <div className="absolute left-[45%] top-[20%] size-7 rounded-full border-2 border-lime-soft shadow-[0_0_18px_rgba(132,255,77,0.65)]" />

                <div className="absolute bottom-6 left-6 right-6 flex items-center justify-between rounded-2xl border border-white/10 bg-black/35 px-4 py-3 backdrop-blur">
                  {swingPhases.map((phase, index) => (
                    <div
                      key={phase}
                      className="flex flex-col items-center gap-2"
                    >
                      <span
                        className={`size-2 rounded-full ${
                          index === 2 ? "bg-lime-soft" : "bg-slate-600"
                        }`}
                      />

                      <span
                        className={`text-[10px] uppercase tracking-wider ${
                          index === 2
                            ? "text-lime-soft"
                            : "text-copy-subtle"
                        }`}
                      >
                        {phase}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Panel>

            <Panel
              className="absolute -bottom-8 -right-4 rounded-3xl backdrop-blur sm:right-6"
              padding="sm"
              variant="raised"
            >
              <p className="text-xs uppercase tracking-[0.2em] text-copy-subtle">
                Swing score
              </p>

              <p className="mt-2 font-display text-5xl font-semibold tracking-[-0.06em] text-white">
                84
              </p>

              <p className="mt-1 text-sm text-lime-soft">
                +6 from last session
              </p>
            </Panel>
          </div>
        </Container>
      </Section>
    </main>
  );
}

export default LandingPage;