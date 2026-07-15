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
    href?: never;
  };

type LinkButtonProps = SharedButtonProps &
  Omit<LinkProps, "children" | "className"> & {
    to: string;
    href?: never;
  };

type AnchorButtonProps = SharedButtonProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "children" | "className"> & {
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

function buildClassName(
  variant: ButtonVariant,
  size: ButtonSize,
  className?: string,
) {
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

function Button(props: ButtonProps) {
  const variant = props.variant ?? "primary";
  const size = props.size ?? "md";

  const resolvedClassName = buildClassName(
    variant,
    size,
    props.className,
  );

  if ("to" in props && typeof props.to === "string") {
    const linkProps = props as LinkButtonProps;

    return (
      <Link
        to={linkProps.to}
        replace={linkProps.replace}
        state={linkProps.state}
        relative={linkProps.relative}
        preventScrollReset={linkProps.preventScrollReset}
        viewTransition={linkProps.viewTransition}
        className={resolvedClassName}
      >
        {linkProps.children}
      </Link>
    );
  }

  if ("href" in props && typeof props.href === "string") {
    const anchorProps = props as AnchorButtonProps;

    return (
      <a
        href={anchorProps.href}
        target={anchorProps.target}
        rel={anchorProps.rel}
        download={anchorProps.download}
        aria-label={anchorProps["aria-label"]}
        className={resolvedClassName}
      >
        {anchorProps.children}
      </a>
    );
  }

  const buttonProps = props as NativeButtonProps;

  return (
    <button
      type={buttonProps.type ?? "button"}
      disabled={buttonProps.disabled}
      form={buttonProps.form}
      name={buttonProps.name}
      value={buttonProps.value}
      onClick={buttonProps.onClick}
      onFocus={buttonProps.onFocus}
      onBlur={buttonProps.onBlur}
      aria-label={buttonProps["aria-label"]}
      aria-pressed={buttonProps["aria-pressed"]}
      className={resolvedClassName}
    >
      {buttonProps.children}
    </button>
  );
}

export default Button;