import {
  BrainCircuit,
  Check,
  Circle,
  ScanLine,
  Sparkles,
  Timer,
} from "lucide-react";

export type ProcessingStepStatus = "pending" | "active" | "complete";

export type ProcessingStep = {
  id: string;
  title: string;
  description: string;
  status: ProcessingStepStatus;
};

type ProcessingStepsProps = {
  steps: ProcessingStep[];
};

const stepIcons = {
  upload: Timer,
  landmarks: ScanLine,
  mechanics: Circle,
  feedback: BrainCircuit,
};

function ProcessingSteps({ steps }: ProcessingStepsProps) {
  return (
    <div className="space-y-3">
      {steps.map((step) => {
        const Icon =
          step.status === "complete"
            ? Check
            : stepIcons[step.id as keyof typeof stepIcons] ?? Sparkles;

        return (
          <div
            key={step.id}
            className={[
              "flex items-start gap-4 rounded-2xl border px-5 py-4 transition-all duration-500",
              step.status === "active"
                ? "border-lime-soft/30 bg-lime-soft/[0.06]"
                : "border-white/8 bg-white/[0.025]",
              step.status === "pending" ? "opacity-45" : "opacity-100",
            ].join(" ")}
          >
            <div
              className={[
                "mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-full transition",
                step.status === "complete"
                  ? "bg-lime-soft text-canvas-deep"
                  : step.status === "active"
                    ? "bg-lime-soft/15 text-lime-soft"
                    : "bg-white/5 text-copy-subtle",
              ].join(" ")}
            >
              <Icon
                className={step.status === "active" ? "animate-pulse" : ""}
                size={19}
              />
            </div>

            <div>
              <p
                className={[
                  "font-semibold transition",
                  step.status === "pending"
                    ? "text-copy-subtle"
                    : "text-white",
                ].join(" ")}
              >
                {step.title}
              </p>

              <p className="mt-1 text-sm leading-6 text-copy-muted">
                {step.description}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default ProcessingSteps;