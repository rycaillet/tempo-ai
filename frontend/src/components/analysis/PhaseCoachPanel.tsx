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
    <div className="h-full rounded-panel border border-white/10 bg-surface p-5 shadow-xl sm:p-6">
      <div className="flex items-start gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
          <Bot size={21} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-display text-lg font-semibold text-white">
              TempoAI Coach
            </p>

            <Badge variant="success">{phase.label}</Badge>
          </div>

          <p className="mt-5 font-display text-2xl font-semibold tracking-[-0.03em] text-white">
            {phase.coaching.headline}
          </p>

          <p className="mt-3 text-sm leading-7 text-copy-muted">
            {phase.coaching.message}
          </p>

          {finding && (
            <div className="mt-6 border-t border-white/10 pt-5">
              <div className="flex items-center gap-2 text-lime-soft">
                <Sparkles size={15} />

                <p className="text-xs font-semibold uppercase tracking-[0.16em]">
                  Recommended focus
                </p>
              </div>

              <div className="mt-3 flex items-center gap-2 text-sm font-semibold text-white">
                <span>{finding.drill.name}</span>
                <ChevronRight size={15} />
              </div>

              <p className="mt-2 text-sm leading-6 text-copy-muted">
                {finding.drill.instructions}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PhaseCoachPanel;