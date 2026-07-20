import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  BrainCircuit,
  CircleAlert,
  Sparkles,
} from "lucide-react";
import {
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import ProcessingSteps, {
  type ProcessingStep,
} from "../components/analysis/ProcessingSteps";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import Section from "../components/ui/Section";
import { getAnalysisRecord } from "../services/analysisService";

const pollingIntervalMs = 1000;

const processingSequence = [
  {
    id: "upload",
    title: "Preparing your video",
    description:
      "Checking the recording and preparing frames for analysis.",
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
  const [searchParams] = useSearchParams();

  const analysisId = searchParams.get("analysisId");
  const missingAnalysisIdError = analysisId
    ? ""
    : "No analysis ID was provided.";

  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!analysisId) {
      return;
    }

    const currentAnalysisId = analysisId;

    let isCancelled = false;
    let timeoutId: number | undefined;

    async function pollAnalysis() {
      try {
        const analysis = await getAnalysisRecord(
          currentAnalysisId,
        );

        if (isCancelled) {
          return;
        }

        if (analysis.status === "COMPLETED") {
          setActiveStep(processingSequence.length);
          setIsComplete(true);

          timeoutId = window.setTimeout(() => {
            navigate(`/analysis/${analysis.id}`, {
              replace: true,
            });
          }, 700);

          return;
        }

        if (analysis.status === "FAILED") {
          setError(
            analysis.failureReason ??
              "TempoAI could not complete this analysis.",
          );
          return;
        }

        setActiveStep((currentStep) =>
          Math.min(
            currentStep + 1,
            processingSequence.length - 1,
          ),
        );

        timeoutId = window.setTimeout(
          pollAnalysis,
          pollingIntervalMs,
        );
      } catch (caughtError) {
        if (isCancelled) {
          return;
        }

        const message =
          caughtError instanceof Error
            ? caughtError.message
            : "TempoAI could not check the analysis status.";

        setError(message);
      }
    }

    void pollAnalysis();

    return () => {
      isCancelled = true;

      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [analysisId, navigate]);

  const displayedError = missingAnalysisIdError || error;

  const steps = useMemo<ProcessingStep[]>(
    () =>
      processingSequence.map((step, index) => ({
        ...step,
        status:
          index < activeStep
            ? "complete"
            : index === activeStep && !isComplete
              ? "active"
              : isComplete
                ? "complete"
                : "pending",
      })),
    [activeStep, isComplete],
  );

  const progress = isComplete
    ? 100
    : Math.min(
        95,
        Math.round(
          ((activeStep + 1) /
            processingSequence.length) *
            100,
        ),
      );

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="narrow">
          <div className="text-center">
            <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-lime-soft/10 text-lime-soft shadow-lime">
              {displayedError ? (
                <CircleAlert size={30} />
              ) : isComplete ? (
                <Sparkles size={30} />
              ) : (
                <BrainCircuit
                  className="animate-pulse"
                  size={30}
                />
              )}
            </div>

            <p className="mt-8 text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
              {displayedError
                ? "Analysis interrupted"
                : isComplete
                  ? "Analysis complete"
                  : "TempoAI is working"}
            </p>

            <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-0.045em] text-white sm:text-5xl">
              {displayedError
                ? "We could not finish your analysis."
                : isComplete
                  ? "Your swing analysis is ready."
                  : "Analyzing your golf swing."}
            </h1>

            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-copy-muted">
              {displayedError
                ? displayedError
                : isComplete
                  ? "Opening your swing report now."
                  : "TempoAI is processing your recording and building a structured performance report."}
            </p>
          </div>

          <Panel
            className="mt-12"
            padding="lg"
            variant="raised"
          >
            <div className="mb-8">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-white">
                  Analysis progress
                </span>

                <span className="font-semibold text-lime-soft">
                  {displayedError
                    ? "Stopped"
                    : `${progress}%`}
                </span>
              </div>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/8">
                <div
                  className="h-full rounded-full bg-lime-soft shadow-lime transition-all duration-700"
                  style={{
                    width: `${progress}%`,
                  }}
                />
              </div>
            </div>

            <ProcessingSteps steps={steps} />

            {displayedError && (
              <div className="mt-8 border-t border-white/10 pt-8">
                <Button
                  className="w-full"
                  onClick={() => navigate("/analysis/new")}
                  size="lg"
                >
                  Return to upload
                </Button>
              </div>
            )}
          </Panel>

          <p className="mt-6 text-center text-sm text-copy-subtle">
            {analysisId
              ? `Analysis ID: ${analysisId}`
              : "Keep this page open while TempoAI processes your recording."}
          </p>
        </Container>
      </Section>
    </main>
  );
}

export default ProcessingPage;