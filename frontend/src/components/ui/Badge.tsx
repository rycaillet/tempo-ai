import type { ReactNode } from "react";

type BadgeVariant = "success" | "info" | "warning" | "neutral";

type BadgeProps = {
  children: ReactNode;
  className?: string;
  variant?: BadgeVariant;
};

const variantClasses: Record<BadgeVariant, string> = {
  success: "bg-lime-soft/10 text-lime-soft",
  info: "bg-ice/10 text-ice",
  warning: "bg-warning/10 text-warning",
  neutral: "bg-white/5 text-copy-muted",
};

function Badge({
  children,
  className,
  variant = "neutral",
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
        variantClasses[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </span>
  );
}

export default Badge;