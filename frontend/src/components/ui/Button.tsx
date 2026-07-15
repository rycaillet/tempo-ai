import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  ReactNode,
} from "react";
import { Link, type LinkProps } from "react-router-dom";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

type SharedButtonProps = {
  children: ReactNode;
  className?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
};

type NativeButtonProps = SharedButtonProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    to?: never;
  };

type LinkButtonProps = SharedButtonProps &
  Omit<LinkProps, "className" | "children"> & {
    to: string;
  };

type AnchorButtonProps = SharedButtonProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    to?: never;
  };

type ButtonProps = NativeButtonProps | LinkButtonProps | AnchorButtonProps;

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-lime !text-canvas-deep shadow-lime hover:bg-lime-bright hover:!text-canvas-deep",
  secondary:
    "border border-white/15 bg-white/5 text-white hover:border-white/25 hover:bg-white/10",
  ghost: "text-copy-muted hover:bg-white/5 hover:text-white",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "min-h-10 px-4 text-sm",
  md: "min-h-12 px-5 text-sm",
  lg: "min-h-14 px-6 text-base",
};

function buildClassName({
  variant,
  size,
  className,
}: Required<Pick<SharedButtonProps, "variant" | "size">> & {
  className?: string;
}) {
  return [
    "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition",
    "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
    variantClasses[variant],
    sizeClasses[size],
    className,
  ]
    .filter(Boolean)
    .join(" ");
}

function Button({
  children,
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  const resolvedClassName = buildClassName({
    variant,
    size,
    className,
  });

  if ("to" in props && props.to) {
    return (
      <Link {...props} className={resolvedClassName}>
        {children}
      </Link>
    );
  }

  if ("href" in props && props.href) {
    return (
      <a {...props} className={resolvedClassName}>
        {children}
      </a>
    );
  }

  return (
    <button {...props} className={resolvedClassName}>
      {children}
    </button>
  );
}

export default Button;