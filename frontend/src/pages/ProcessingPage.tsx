import {
  useEffect,
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

const processingSequence: ProcessingStep[] = [
  {
    id: "video",
    title: "Preparing your video",
    description:
      "Reading the recording and preparing video frames for computer-vision analysis.",
  },
  {
    id: "landmarks",
    title: "Detecting body landmarks",
    description:
      "Tracking shoulders, hips, knees, hands, and other key body positions throughout the swing.",
  },
  {
    id: "phases",
    title: "Identifying swing phases",
    description:
      "Locating address, takeaway, top, downswing, impact, and finish reference points.",
  },
  {
    id: "mechanics",
    title: "Measuring swing mechanics",
    description:
      "Evaluating tempo, posture, rotation, weight shift, stability, and impact mechanics.",
  },
  {
    id: "club",
    title: "Analyzing club geometry",
    description:
      "Detecting and tracking the shaft to support club-based measurements when reliable geometry is available.",
  },
  {
    id: "report",
    title: "Building your coaching report",
    description:
      "Combining measured observations, scoring, findings, and practice recommendations into your final report.",
  },
];

function ProcessingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const analysisId = searchParams.get("analysisId");

  const missingAnalysisIdError = analysisId
    ? ""
    : "No analysis ID was provided.";

  const [error, setError] = useState("");
  const [isComplete, setIsComplete] =
    useState(false);

  useEffect(() => {
    if (!analysisId) {
      return;
    }

    const currentAnalysisId = analysisId;

    let isCancelled = false;
    let timeoutId: number | undefined;

    async function pollAnalysis() {
      try {
        const analysis =
          await getAnalysisRecord(
            currentAnalysisId,
          );

        if (isCancelled) {
          return;
        }

        if (analysis.status === "COMPLETED") {
          setIsComplete(true);

          timeoutId = window.setTimeout(
            () => {
              navigate(
                `/analysis/${analysis.id}`,
                {
                  replace: true,
                },
              );
            },
            700,
          );

          return;
        }

        if (analysis.status === "FAILED") {
          setError(
            analysis.failureReason ??
              "TempoAI could not complete this analysis.",
          );

          return;
        }

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

  const displayedError =
    missingAnalysisIdError || error;

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
                  : "Computer vision processing"}
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
                  : "TempoAI is running computer-vision analysis across your recording. Full analysis can take several minutes depending on video length and processing hardware."}
            </p>
          </div>

          <Panel
            className="mt-12"
            padding="lg"
            variant="raised"
          >
            {!displayedError && !isComplete && (
              <div className="mb-8 rounded-2xl border border-ice/15 bg-ice/[0.04] px-5 py-4">
                <div className="flex items-center gap-3">
                  <span className="relative flex size-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-lime-soft opacity-40" />
                    <span className="relative inline-flex size-3 rounded-full bg-lime-soft" />
                  </span>

                  <p className="font-semibold text-white">
                    Analysis in progress
                  </p>
                </div>

                <p className="mt-2 text-sm leading-6 text-copy-muted">
                  TempoAI processes the complete
                  recording before generating the final
                  coaching report.
                </p>
              </div>
            )}

            {isComplete && !displayedError && (
              <div className="mb-8 rounded-2xl border border-lime-soft/20 bg-lime-soft/[0.05] px-5 py-4">
                <div className="flex items-center gap-3">
                  <Sparkles
                    className="text-lime-soft"
                    size={19}
                  />

                  <p className="font-semibold text-white">
                    Analysis complete
                  </p>
                </div>

                <p className="mt-2 text-sm leading-6 text-copy-muted">
                  Your measurements and coaching report
                  are ready.
                </p>
              </div>
            )}

            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                Analysis pipeline
              </p>

              <p className="mt-2 text-sm leading-6 text-copy-muted">
                TempoAI runs these processing stages
                across your uploaded swing.
              </p>
            </div>

            <div className="mt-6">
              <ProcessingSteps
                steps={processingSequence}
                isComplete={isComplete}
              />
            </div>

            {displayedError && (
              <div className="mt-8 border-t border-white/10 pt-8">
                <Button
                  className="w-full"
                  onClick={() =>
                    navigate("/analysis/new")
                  }
                  size="lg"
                >
                  Return to upload
                </Button>
              </div>
            )}
          </Panel>

          {!displayedError && !isComplete && (
            <p className="mx-auto mt-6 max-w-xl text-center text-sm leading-6 text-copy-subtle">
              Full analysis can take several minutes.
              TempoAI is processing real video,
              pose, motion, geometry, and club
              detection data rather than displaying
              estimated progress.
            </p>
          )}
        </Container>
      </Section>
    </main>
  );
}

export default ProcessingPage;