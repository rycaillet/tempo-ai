import type { ReactNode } from "react";

type ScoreRingProps = {
  score: number;
  label: string;
  subtitle?: string;
  icon?: ReactNode;
};

function ScoreRing({
  score,
  label,
  subtitle,
  icon,
}: ScoreRingProps) {
  const percentage = Math.max(0, Math.min(score, 100));

  const circumference = 2 * Math.PI * 72;

  const dashOffset =
    circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex h-52 w-52 items-center justify-center">
        <svg
          className="-rotate-90 absolute"
          width="180"
          height="180"
        >
          <circle
            cx="90"
            cy="90"
            r="72"
            fill="transparent"
            stroke="rgba(255,255,255,.08)"
            strokeWidth="12"
          />

          <circle
            cx="90"
            cy="90"
            r="72"
            fill="transparent"
            stroke="#9cff63"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{
              transition:
                "stroke-dashoffset .7s cubic-bezier(.22,1,.36,1)",
            }}
          />
        </svg>

        <div className="flex flex-col items-center">
          {icon}

          <p className="font-display text-6xl font-bold text-white">
            {score}
          </p>

          <p className="mt-1 text-sm uppercase tracking-[0.2em] text-copy-subtle">
            {label}
          </p>
        </div>
      </div>

      {subtitle && (
        <p className="mt-5 rounded-full bg-lime-soft/10 px-4 py-2 text-sm font-medium text-lime-soft">
          {subtitle}
        </p>
      )}
    </div>
  );
}

export default ScoreRing;