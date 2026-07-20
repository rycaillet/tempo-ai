import { Bot, ChevronRight, Sparkles } from "lucide-react";

import type {
  SwingFinding,
  SwingPhase,
} from "../../types/analysis";
import Badge from "../ui/Badge";

type PhaseCoachPanelProps = {
  phase: SwingPhase;
  finding?: SwingFinding;
};

function PhaseCoachPanel({
  phase,
  finding,
}: PhaseCoachPanelProps) {
  return (
    <div className="absolute left-5 top-5 z-10 max-w-sm rounded-2xl border border-white/10 bg-black/55 p-4 shadow-xl backdrop-blur-md">
      <div className="flex items-start gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-lime-soft/10 text-lime-soft">
          <Bot size={20} />
        </div>

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-white">
              TempoAI Coach
            </p>

            <Badge variant="success">{phase.label}</Badge>
          </div>

          <p className="mt-3 font-display text-lg font-semibold text-white">
            {phase.coaching.headline}
          </p>

          <p className="mt-2 text-sm leading-6 text-copy-muted">
            {phase.coaching.message}
          </p>

          {finding && (
            <div className="mt-4 border-t border-white/10 pt-4">
              <div className="flex items-center gap-2 text-lime-soft">
                <Sparkles size={15} />

                <p className="text-xs font-semibold uppercase tracking-[0.16em]">
                  Recommended focus
                </p>
              </div>

              <div className="mt-2 flex items-center gap-2 text-sm font-medium text-white">
                <span>{finding.drill.name}</span>
                <ChevronRight size={15} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PhaseCoachPanel;