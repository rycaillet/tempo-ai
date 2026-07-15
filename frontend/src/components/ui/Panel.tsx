import type { HTMLAttributes, ReactNode } from "react";

type PanelVariant = "default" | "raised" | "muted" | "glass";

type PanelProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  className?: string;
  variant?: PanelVariant;
  padding?: "none" | "sm" | "md" | "lg";
};

const variantClasses: Record<PanelVariant, string> = {
  default: "border border-white/10 bg-surface",
  raised: "border border-white/10 bg-surface-raised shadow-panel",
  muted: "border border-white/5 bg-surface-muted",
  glass: "border border-white/10 bg-black/35 backdrop-blur",
};

const paddingClasses = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

function Panel({
  children,
  className,
  variant = "default",
  padding = "md",
  ...props
}: PanelProps) {
  return (
    <div
      {...props}
      className={[
        "rounded-panel",
        variantClasses[variant],
        paddingClasses[padding],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}

export default Panel;