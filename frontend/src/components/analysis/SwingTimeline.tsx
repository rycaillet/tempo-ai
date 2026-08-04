import type {
  ChangeEvent,
  KeyboardEvent,
} from "react";

import type { SwingPhase } from "../../types/analysis";

type SwingTimelineProps = {
  phases: SwingPhase[];
  currentTime: number;
  duration: number;
  selectedPhaseId: string;
  onPhaseSelect: (phase: SwingPhase) => void;
  onSeek: (timeSeconds: number) => void;
};

function clampTime(
  value: number,
  duration: number,
) {
  if (!Number.isFinite(value)) {
    return 0;
  }

  if (
    !Number.isFinite(duration) ||
    duration <= 0
  ) {
    return Math.max(0, value);
  }

  return Math.min(
    duration,
    Math.max(0, value),
  );
}

function getPhaseTime(
  phase: SwingPhase,
  duration: number,
) {
  const parsedTimestamp = Number.parseFloat(
    phase.timestamp.replace("s", ""),
  );

  return clampTime(
    Number.isFinite(parsedTimestamp)
      ? parsedTimestamp
      : 0,
    duration,
  );
}

function formatTimelineTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "0:00.0";
  }

  const wholeMinutes = Math.floor(
    seconds / 60,
  );
  const remainingSeconds =
    seconds - wholeMinutes * 60;

  return `${wholeMinutes}:${remainingSeconds
    .toFixed(1)
    .padStart(4, "0")}`;
}

function getMarkerPosition(
  phase: SwingPhase,
  duration: number,
  phaseIndex: number,
  phaseCount: number,
) {
  if (duration > 0) {
    return Math.min(
      100,
      Math.max(
        0,
        (getPhaseTime(phase, duration) /
          duration) *
          100,
      ),
    );
  }

  if (phaseCount <= 1) {
    return 0;
  }

  return (
    phaseIndex /
    (phaseCount - 1)
  ) * 100;
}

function SwingTimeline({
  phases,
  currentTime,
  duration,
  selectedPhaseId,
  onPhaseSelect,
  onSeek,
}: SwingTimelineProps) {
  const normalizedDuration =
    Number.isFinite(duration) &&
    duration > 0
      ? duration
      : 0;

  const normalizedCurrentTime =
    clampTime(
      currentTime,
      normalizedDuration,
    );

  const progressPercentage =
    normalizedDuration > 0
      ? (
          normalizedCurrentTime /
          normalizedDuration
        ) * 100
      : 0;

  function handleSeek(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    onSeek(
      Number.parseFloat(
        event.target.value,
      ),
    );
  }

  function handleTimelineKeyDown(
    event: KeyboardEvent<HTMLInputElement>,
  ) {
    if (
      event.key !== "ArrowLeft" &&
      event.key !== "ArrowRight"
    ) {
      return;
    }

    event.preventDefault();

    const adjustment =
      event.key === "ArrowRight"
        ? 0.1
        : -0.1;

    onSeek(
      clampTime(
        normalizedCurrentTime +
          adjustment,
        normalizedDuration,
      ),
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-copy-subtle">
            Swing timeline
          </p>

          <p className="mt-1 text-sm text-copy-muted">
            Drag the playhead or select a detected phase.
          </p>
        </div>

        <p className="shrink-0 font-mono text-xs text-copy-subtle">
          {formatTimelineTime(
            normalizedCurrentTime,
          )}
          {" / "}
          {formatTimelineTime(
            normalizedDuration,
          )}
        </p>
      </div>

      <div className="relative mt-8 px-3">
        <div className="pointer-events-none absolute left-3 right-3 top-3 h-1 rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-lime-soft transition-[width] duration-100"
            style={{
              width: `${progressPercentage}%`,
            }}
          />
        </div>

        <input
          aria-label="Swing video timeline"
          className="relative z-20 h-7 w-full cursor-pointer appearance-none bg-transparent accent-lime-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-lime-soft/60"
          max={
            normalizedDuration > 0
              ? normalizedDuration
              : 1
          }
          min="0"
          onChange={handleSeek}
          onKeyDown={
            handleTimelineKeyDown
          }
          step="0.01"
          type="range"
          value={
            normalizedDuration > 0
              ? normalizedCurrentTime
              : 0
          }
        />

        <div className="relative mt-4 h-16">
          {phases.map(
            (
              phase,
              phaseIndex,
            ) => {
              const position =
                getMarkerPosition(
                  phase,
                  normalizedDuration,
                  phaseIndex,
                  phases.length,
                );

              const isSelected =
                phase.id ===
                selectedPhaseId;

              return (
                <button
                  key={phase.id}
                  aria-label={`Jump to ${phase.label} at ${phase.timestamp}`}
                  aria-pressed={
                    isSelected
                  }
                  className="group absolute top-0 -translate-x-1/2 text-center focus:outline-none"
                  style={{
                    left: `${position}%`,
                  }}
                  type="button"
                  onClick={() =>
                    onPhaseSelect(phase)
                  }
                >
                  <span
                    className={[
                      "mx-auto block size-3 rounded-full border-2 transition",
                      isSelected
                        ? "scale-125 border-lime-soft bg-lime-soft shadow-[0_0_14px_rgba(132,255,77,0.7)]"
                        : "border-copy-subtle bg-surface-raised group-hover:border-white group-focus-visible:border-white",
                    ].join(" ")}
                  />

                  <span
                    className={[
                      "mt-3 block whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.12em] transition",
                      isSelected
                        ? "text-lime-soft"
                        : "text-copy-subtle group-hover:text-white group-focus-visible:text-white",
                    ].join(" ")}
                  >
                    {phase.label}
                  </span>

                  <span className="mt-1 block text-[10px] text-copy-subtle">
                    {phase.timestamp}
                  </span>
                </button>
              );
            },
          )}
        </div>
      </div>
    </div>
  );
}

export default SwingTimeline;