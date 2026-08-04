import type { ReactNode } from "react";

type ScoreRingProps = {
  score: number;
  label: string;
  rating?: string | null;
  subtitle?: string;
  icon?: ReactNode;
};

function getFallbackRating(score: number) {
  if (score >= 90) {
    return "Elite";
  }

  if (score >= 80) {
    return "Excellent";
  }

  if (score >= 70) {
    return "Good";
  }

  if (score >= 60) {
    return "Average";
  }

  return "Needs Work";
}

function ScoreRing({
  score,
  label,
  rating,
  subtitle,
  icon,
}: ScoreRingProps) {
  const percentage = Math.max(
    0,
    Math.min(score, 100),
  );

  const radius = 82;
  const circumference =
    2 * Math.PI * radius;

  const dashOffset =
    circumference -
    (percentage / 100) * circumference;

  const displayedRating =
    rating?.trim() || getFallbackRating(score);

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex h-64 w-64 items-center justify-center">
        <div className="absolute h-40 w-40 rounded-full bg-lime-soft/10 blur-3xl" />

        <svg
          className="-rotate-90 absolute"
          width="220"
          height="220"
        >
          <circle
            cx="110"
            cy="110"
            r={radius}
            fill="transparent"
            stroke="rgba(255,255,255,.08)"
            strokeWidth="12"
          />

          <circle
            cx="110"
            cy="110"
            r={radius}
            fill="transparent"
            stroke="#9cff63"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{
              transition:
                "stroke-dashoffset .8s cubic-bezier(.22,1,.36,1)",
            }}
          />
        </svg>

        <div className="relative z-10 flex flex-col items-center">
          {icon}

          <p className="font-display text-7xl font-bold leading-none text-white">
            {score}
          </p>
        </div>
      </div>

      <h3 className="font-display text-xl font-semibold text-white">
        {label}
      </h3>

      <p className="mt-1 text-sm font-medium text-lime-soft">
        {displayedRating}
      </p>

      {subtitle && (
        <div className="mt-5 rounded-full bg-lime-soft/10 px-5 py-2">
          <p className="text-sm font-semibold text-lime-soft">
            {subtitle}
          </p>
        </div>
      )}
    </div>
  );
}

export default ScoreRing;