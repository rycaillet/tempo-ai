import {
  BrainCircuit,
  Check,
  CircleDot,
  Gauge,
  ScanLine,
  Target,
  Timer,
} from "lucide-react";

export type ProcessingStep = {
  id: string;
  title: string;
  description: string;
};

type ProcessingStepsProps = {
  steps: ProcessingStep[];
  isComplete: boolean;
};

const stepIcons = {
  video: Timer,
  landmarks: ScanLine,
  phases: Target,
  mechanics: Gauge,
  club: CircleDot,
  report: BrainCircuit,
};

function ProcessingSteps({
  steps,
  isComplete,
}: ProcessingStepsProps) {
  return (
    <div className="space-y-3">
      {steps.map((step) => {
        const StageIcon =
          stepIcons[
            step.id as keyof typeof stepIcons
          ] ?? BrainCircuit;

        const Icon = isComplete
          ? Check
          : StageIcon;

        return (
          <div
            key={step.id}
            className={[
              "flex items-start gap-4 rounded-2xl border px-5 py-4 transition-all duration-500",
              isComplete
                ? "border-lime-soft/15 bg-lime-soft/[0.035]"
                : "border-white/8 bg-white/[0.025]",
            ].join(" ")}
          >
            <div
              className={[
                "mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-full transition",
                isComplete
                  ? "bg-lime-soft text-canvas-deep"
                  : "bg-ice/10 text-ice",
              ].join(" ")}
            >
              <Icon size={19} />
            </div>

            <div>
              <p className="font-semibold text-white">
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