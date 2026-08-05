import {
  CalendarDays,
  LogOut,
  Mail,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";

import Button from "../components/ui/Button";
import { useAuth } from "../hooks/useAuth";

type ProfileDetailProps = {
  icon: ReactNode;
  label: string;
  value: string;
};

function formatAccountDate(
  dateValue: string,
): string {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function ProfileDetail({
  icon,
  label,
  value,
}: ProfileDetailProps) {
  return (
    <div className="flex items-start gap-4 rounded-2xl border border-white/10 bg-black/10 p-4">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-lime-soft/10 text-lime-soft">
        {icon}
      </div>

      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-copy-subtle">
          {label}
        </p>

        <p className="mt-1 break-words text-sm font-semibold text-white">
          {value}
        </p>
      </div>
    </div>
  );
}

function ProfilePage() {
  const navigate = useNavigate();

  const {
    user,
    logout,
  } = useAuth();

  const [error, setError] = useState("");

  const [
    isLoggingOut,
    setIsLoggingOut,
  ] = useState(false);

  async function handleLogout() {
    if (isLoggingOut) {
      return;
    }

    try {
      setError("");
      setIsLoggingOut(true);

      await logout();

      navigate("/login", {
        replace: true,
      });
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "TempoAI could not sign you out.",
      );
    } finally {
      setIsLoggingOut(false);
    }
  }

  if (!user) {
    return null;
  }

  const initials = user.displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  return (
    <main className="min-h-screen bg-canvas px-4 py-10 text-copy sm:px-6 sm:py-14 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <section className="overflow-hidden rounded-panel-large border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(132,255,77,0.14),transparent_35%),linear-gradient(135deg,rgba(17,38,29,0.98),rgba(8,20,15,0.98))] p-6 shadow-panel sm:p-8 lg:p-10">
          <div className="flex flex-col gap-8 sm:flex-row sm:items-center">
            <div className="flex size-20 shrink-0 items-center justify-center rounded-3xl border border-lime-soft/20 bg-lime-soft/10 font-display text-2xl font-semibold text-lime-soft">
              {initials || (
                <UserRound size={30} />
              )}
            </div>

            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                Account preferences
              </p>

              <h1 className="mt-3 font-display text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl">
                {user.displayName}
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-copy-muted sm:text-base">
                Review your TempoAI account information
                and manage your active session.
              </p>
            </div>
          </div>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <section className="rounded-panel border border-white/10 bg-surface-raised p-6 shadow-panel sm:p-8">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                <UserRound size={20} />
              </div>

              <div>
                <h2 className="font-display text-xl font-semibold text-white">
                  Account details
                </h2>

                <p className="mt-1 text-sm text-copy-muted">
                  Information associated with your account.
                </p>
              </div>
            </div>

            <div className="mt-7 grid gap-4 sm:grid-cols-2">
              <ProfileDetail
                icon={<UserRound size={18} />}
                label="Display name"
                value={user.displayName}
              />

              <ProfileDetail
                icon={<Mail size={18} />}
                label="Email address"
                value={user.email}
              />

              <ProfileDetail
                icon={<CalendarDays size={18} />}
                label="Account created"
                value={formatAccountDate(
                  user.createdAt,
                )}
              />

              <ProfileDetail
                icon={<ShieldCheck size={18} />}
                label="Session security"
                value="Secure server session"
              />
            </div>
          </section>

          <aside className="rounded-panel border border-white/10 bg-surface-raised p-6 shadow-panel sm:p-8">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
              <ShieldCheck size={20} />
            </div>

            <h2 className="mt-5 font-display text-xl font-semibold text-white">
              Secure account
            </h2>

            <p className="mt-3 text-sm leading-6 text-copy-muted">
              Your password is stored as an Argon2id
              hash, and your login is managed through
              a protected server-side session.
            </p>

            <div className="mt-6 border-t border-white/10 pt-6">
              <h3 className="text-sm font-semibold text-white">
                Sign out of TempoAI
              </h3>

              <p className="mt-2 text-sm leading-6 text-copy-muted">
                This invalidates your current session
                on the server.
              </p>

              {error && (
                <p className="mt-4 rounded-xl border border-red-400/20 bg-red-400/5 p-3 text-sm text-red-200">
                  {error}
                </p>
              )}

              <Button
                className="mt-5 w-full"
                disabled={isLoggingOut}
                type="button"
                variant="secondary"
                onClick={handleLogout}
              >
                <LogOut size={17} />

                {isLoggingOut
                  ? "Signing out"
                  : "Sign out"}
              </Button>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}

export default ProfilePage;