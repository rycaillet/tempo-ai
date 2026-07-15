import type { ReactNode } from "react";

import Panel from "./Panel";

type MetricCardProps = {
  title: string;
  value: string;
  trend?: string;
  icon?: ReactNode;
};

function MetricCard({
  title,
  value,
  trend,
  icon,
}: MetricCardProps) {
  return (
    <Panel variant="raised">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-copy-subtle">
            {title}
          </p>

          <p className="mt-3 font-display text-4xl font-bold text-white">
            {value}
          </p>

          {trend && (
            <p className="mt-2 text-sm text-lime-soft">
              {trend}
            </p>
          )}
        </div>

        {icon && (
          <div className="rounded-2xl bg-lime-soft/10 p-3">
            {icon}
          </div>
        )}
      </div>
    </Panel>
  );
}

export default MetricCard;