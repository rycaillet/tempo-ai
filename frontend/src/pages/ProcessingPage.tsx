import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

import ProcessingSteps, {
  type ProcessingStep,
} from "../components/analysis/ProcessingSteps";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import Section from "../components/ui/Section";

const processingSequence = [
  {
    id: "upload",
    title: "Preparing your video",
    description: "Checking the recording and preparing frames for analysis.",
  },
  {
    id: "landmarks",
    title: "Detecting body landmarks",
    description:
      "Tracking your shoulders, hips, knees, hands, and other key positions.",
  },
  {
    id: "mechanics",
    title: "Measuring swing mechanics",
    description:
      "Evaluating posture, tempo, rotation, balance, and movement patterns.",
  },
  {
    id: "feedback",
    title: "Generating coaching feedback",
    description:
      "Turning your swing data into focused observations and practice drills.",
  },
];

function ProcessingPage() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const isComplete = activeStep >= processingSequence.length;

  useEffect(() => {
    if (isComplete) {
      return;
    }

    const timer = window.setTimeout(() => {
      setActiveStep((currentStep) => currentStep + 1);
    }, 1500);

    return () => {
      window.clearTimeout(timer);
    };
  }, [activeStep, isComplete]);

  const steps = useMemo<ProcessingStep[]>(
    () =>
      processingSequence.map((step, index) => ({
        ...step,
        status:
          index < activeStep
            ? "complete"
            : index === activeStep
              ? "active"
              : "pending",
      })),
    [activeStep],
  );

  const progress = Math.min(
    100,
    Math.round((activeStep / processingSequence.length) * 100),
  );

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="narrow">
          <div className="text-center">
            <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-lime-soft/10 text-lime-soft shadow-lime">
              {isComplete ? (
                <Sparkles size={30} />
              ) : (
                <BrainCircuit className="animate-pulse" size={30} />
              )}
            </div>

            <p className="mt-8 text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
              {isComplete ? "Analysis complete" : "TempoAI is working"}
            </p>

            <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-0.045em] text-white sm:text-5xl">
              {isComplete
                ? "Your swing analysis is ready."
                : "Analyzing your golf swing."}
            </h1>

            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-copy-muted">
              {isComplete
                ? "Review your swing score, movement metrics, coaching priorities, and recommended drills."
                : "TempoAI is processing your recording and building a structured performance report."}
            </p>
          </div>

          <Panel className="mt-12" padding="lg" variant="raised">
            <div className="mb-8">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-white">
                  Analysis progress
                </span>

                <span className="font-semibold text-lime-soft">
                  {progress}%
                </span>
              </div>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/8">
                <div
                  className="h-full rounded-full bg-lime-soft shadow-lime transition-all duration-700"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <ProcessingSteps steps={steps} />

            {isComplete && (
              <div className="mt-8 border-t border-white/10 pt-8">
                <Button
                  className="w-full"
                  onClick={() => navigate("/analysis/demo-swing")}
                  size="lg"
                >
                  View analysis results
                </Button>
              </div>
            )}
          </Panel>

          <p className="mt-6 text-center text-sm text-copy-subtle">
            Keep this page open while TempoAI processes your recording.
          </p>
        </Container>
      </Section>
    </main>
  );
}

export default ProcessingPage;