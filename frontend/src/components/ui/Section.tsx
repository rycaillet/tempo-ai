import type { ElementType, ReactNode } from "react";

type SectionProps = {
  children: ReactNode;
  className?: string;
  as?: ElementType;
  spacing?: "sm" | "md" | "lg";
};

const spacingClasses = {
  sm: "py-10",
  md: "py-16",
  lg: "py-24",
};

function Section({
  children,
  className,
  as: Component = "section",
  spacing = "md",
}: SectionProps) {
  return (
    <Component
      className={[spacingClasses[spacing], className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </Component>
  );
}

export default Section;