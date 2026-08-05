import {
  ArrowRight,
  CircleAlert,
  Eye,
  EyeOff,
  LoaderCircle,
  LockKeyhole,
  Mail,
  UserRound,
} from "lucide-react";
import {
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import Button from "../components/ui/Button";
import { useAuth } from "../hooks/useAuth";

function RegisterPage() {
  const navigate = useNavigate();

  const { register } = useAuth();

  const [displayName, setDisplayName] =
    useState("");

  const [email, setEmail] = useState("");

  const [password, setPassword] =
    useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [
    showConfirmPassword,
    setShowConfirmPassword,
  ] = useState(false);

  const [error, setError] = useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    if (password !== confirmPassword) {
      setError(
        "The two passwords do not match.",
      );

      return;
    }

    try {
      setError("");
      setIsSubmitting(true);

      await register({
        displayName,
        email,
        password,
      });

      navigate("/dashboard", {
        replace: true,
      });
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "TempoAI could not create your account.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6 py-12 text-copy">
      <div className="w-full max-w-md">
        <Link
          className="inline-flex items-center font-display text-2xl font-semibold tracking-[-0.04em] text-white"
          to="/"
        >
          Tempo
          <span className="text-lime-soft">
            AI
          </span>
        </Link>

        <div className="mt-10 rounded-panel border border-white/10 bg-surface-raised p-6 shadow-panel sm:p-8">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
            <UserRound size={22} />
          </div>

          <h1 className="mt-6 font-display text-4xl font-semibold tracking-[-0.04em] text-white">
            Create your account
          </h1>

          <p className="mt-3 text-sm leading-6 text-copy-muted">
            Build a private swing history and track
            your improvement over time.
          </p>

          {error && (
            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-red-400/20 bg-red-400/5 p-4">
              <CircleAlert
                className="mt-0.5 shrink-0 text-red-300"
                size={18}
              />

              <p className="text-sm leading-6 text-red-200">
                {error}
              </p>
            </div>
          )}

          <form
            className="mt-8 space-y-5"
            onSubmit={handleSubmit}
          >
            <label className="block">
              <span className="text-sm font-semibold text-white">
                Display name
              </span>

              <div className="relative mt-2">
                <UserRound
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                  size={18}
                />

                <input
                  autoComplete="name"
                  className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-4 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                  maxLength={80}
                  minLength={2}
                  name="displayName"
                  placeholder="Your name"
                  required
                  type="text"
                  value={displayName}
                  onChange={(event) =>
                    setDisplayName(
                      event.target.value,
                    )
                  }
                />
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-white">
                Email address
              </span>

              <div className="relative mt-2">
                <Mail
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                  size={18}
                />

                <input
                  autoComplete="email"
                  className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-4 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                  inputMode="email"
                  maxLength={254}
                  name="email"
                  placeholder="you@example.com"
                  required
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value,
                    )
                  }
                />
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-white">
                Password
              </span>

              <div className="relative mt-2">
                <LockKeyhole
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                  size={18}
                />

                <input
                  autoComplete="new-password"
                  className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-20 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                  maxLength={128}
                  minLength={12}
                  name="password"
                  placeholder="At least 12 characters"
                  required
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(
                      event.target.value,
                    )
                  }
                />

                <button
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  className="absolute right-4 top-1/2 flex -translate-y-1/2 items-center gap-1.5 text-xs font-medium text-copy-muted transition hover:text-white focus:outline-none focus-visible:text-white"
                  type="button"
                  onClick={() =>
                    setShowPassword(
                      (currentValue) =>
                        !currentValue,
                    )
                  }
                >
                  {showPassword ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}

                  {showPassword
                    ? "Hide"
                    : "Show"}
                </button>
              </div>

              <p className="mt-2 text-xs leading-5 text-copy-subtle">
                Use at least 12 characters. A
                memorable passphrase works well.
              </p>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-white">
                Confirm password
              </span>

              <div className="relative mt-2">
                <LockKeyhole
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                  size={18}
                />

                <input
                  autoComplete="new-password"
                  className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-20 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                  maxLength={128}
                  minLength={12}
                  name="confirmPassword"
                  placeholder="Enter it again"
                  required
                  type={
                    showConfirmPassword
                      ? "text"
                      : "password"
                  }
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(
                      event.target.value,
                    )
                  }
                />

                <button
                  aria-label={
                    showConfirmPassword
                      ? "Hide confirmed password"
                      : "Show confirmed password"
                  }
                  className="absolute right-4 top-1/2 flex -translate-y-1/2 items-center gap-1.5 text-xs font-medium text-copy-muted transition hover:text-white focus:outline-none focus-visible:text-white"
                  type="button"
                  onClick={() =>
                    setShowConfirmPassword(
                      (currentValue) =>
                        !currentValue,
                    )
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}

                  {showConfirmPassword
                    ? "Hide"
                    : "Show"}
                </button>
              </div>
            </label>

            <Button
              className="w-full"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? (
                <>
                  <LoaderCircle
                    className="animate-spin"
                    size={18}
                  />
                  Creating account
                </>
              ) : (
                <>
                  Create account
                  <ArrowRight size={17} />
                </>
              )}
            </Button>
          </form>

          <p className="mt-7 text-center text-sm text-copy-muted">
            Already have an account?{" "}
            <Link
              className="font-semibold text-lime-soft transition hover:text-white"
              to="/login"
            >
              Sign in
            </Link>
          </p>
        </div>

        <p className="mt-6 text-center text-xs leading-5 text-copy-subtle">
          Your swing history is private and tied
          to your TempoAI account.
        </p>
      </div>
    </main>
  );
}

export default RegisterPage;