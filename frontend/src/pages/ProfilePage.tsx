import {
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  LogOut,
  Mail,
  Save,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  useState,
  type FormEvent,
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
  const date = new Date(
    dateValue,
  );

  if (
    Number.isNaN(date.getTime())
  ) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "long",
      day: "numeric",
      year: "numeric",
    },
  ).format(date);
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
  const navigate =
    useNavigate();

  const {
    user,
    updateProfile,
    changePassword,
    logout,
  } = useAuth();

  const [
    displayName,
    setDisplayName,
  ] = useState(
    user?.displayName ?? "",
  );

  const [
    currentPassword,
    setCurrentPassword,
  ] = useState("");

  const [
    newPassword,
    setNewPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [
    showCurrentPassword,
    setShowCurrentPassword,
  ] = useState(false);

  const [
    showNewPassword,
    setShowNewPassword,
  ] = useState(false);

  const [
    showConfirmPassword,
    setShowConfirmPassword,
  ] = useState(false);

  const [
    profileError,
    setProfileError,
  ] = useState("");

  const [
    profileSuccess,
    setProfileSuccess,
  ] = useState("");

  const [
    passwordError,
    setPasswordError,
  ] = useState("");

  const [
    passwordSuccess,
    setPasswordSuccess,
  ] = useState("");

  const [
    logoutError,
    setLogoutError,
  ] = useState("");

  const [
    isSavingProfile,
    setIsSavingProfile,
  ] = useState(false);

  const [
    isChangingPassword,
    setIsChangingPassword,
  ] = useState(false);

  const [
    isLoggingOut,
    setIsLoggingOut,
  ] = useState(false);

  async function handleProfileSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      !user ||
      isSavingProfile
    ) {
      return;
    }

    const normalizedDisplayName =
      displayName.trim();

    if (
      normalizedDisplayName.length <
      2
    ) {
      setProfileError(
        "Display name must be at least 2 characters.",
      );

      return;
    }

    if (
      normalizedDisplayName.length >
      80
    ) {
      setProfileError(
        "Display name must be 80 characters or fewer.",
      );

      return;
    }

    if (
      normalizedDisplayName ===
      user.displayName
    ) {
      setProfileError("");
      setProfileSuccess(
        "Your display name is already up to date.",
      );

      return;
    }

    try {
      setProfileError("");
      setProfileSuccess("");
      setIsSavingProfile(true);

      await updateProfile({
        displayName:
          normalizedDisplayName,
      });

      setProfileSuccess(
        "Your display name was updated.",
      );
    } catch (caughtError) {
      setProfileError(
        caughtError instanceof Error
          ? caughtError.message
          : "TempoAI could not update your profile.",
      );
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      isChangingPassword
    ) {
      return;
    }

    if (
      newPassword !==
      confirmPassword
    ) {
      setPasswordError(
        "The new passwords do not match.",
      );

      return;
    }

    if (
      newPassword.length < 12
    ) {
      setPasswordError(
        "Your new password must be at least 12 characters.",
      );

      return;
    }

    if (
      newPassword.length > 128
    ) {
      setPasswordError(
        "Your new password must be 128 characters or fewer.",
      );

      return;
    }

    try {
      setPasswordError("");
      setPasswordSuccess("");
      setIsChangingPassword(
        true,
      );

      const message =
        await changePassword({
          currentPassword,
          newPassword,
        });

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      setShowCurrentPassword(
        false,
      );
      setShowNewPassword(false);
      setShowConfirmPassword(
        false,
      );

      setPasswordSuccess(
        message,
      );
    } catch (caughtError) {
      setPasswordError(
        caughtError instanceof Error
          ? caughtError.message
          : "TempoAI could not change your password.",
      );
    } finally {
      setIsChangingPassword(
        false,
      );
    }
  }

  async function handleLogout() {
    if (isLoggingOut) {
      return;
    }

    try {
      setLogoutError("");
      setIsLoggingOut(true);

      await logout();

      navigate("/login", {
        replace: true,
      });
    } catch (caughtError) {
      setLogoutError(
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

  const initials =
    user.displayName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(
        (part) =>
          part[0]?.toUpperCase(),
      )
      .join("");

  return (
    <main className="min-h-screen bg-canvas px-4 py-10 text-copy sm:px-6 sm:py-14 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <section className="overflow-hidden rounded-panel-large border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(132,255,77,0.14),transparent_35%),linear-gradient(135deg,rgba(17,38,29,0.98),rgba(8,20,15,0.98))] p-6 shadow-panel sm:p-8 lg:p-10">
          <div className="flex flex-col gap-8 sm:flex-row sm:items-center">
            <div className="flex size-20 shrink-0 items-center justify-center rounded-3xl border border-lime-soft/20 bg-lime-soft/10 font-display text-2xl font-semibold text-lime-soft">
              {initials || (
                <UserRound
                  size={30}
                />
              )}
            </div>

            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                Account settings
              </p>

              <h1 className="mt-3 font-display text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl">
                {user.displayName}
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-copy-muted sm:text-base">
                Manage your public display
                name, account password, and
                active TempoAI session.
              </p>
            </div>
          </div>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="grid gap-6">
            <section className="rounded-panel border border-white/10 bg-surface-raised p-6 shadow-panel sm:p-8">
              <div className="flex items-center gap-3">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                  <UserRound
                    size={20}
                  />
                </div>

                <div>
                  <h2 className="font-display text-xl font-semibold text-white">
                    Profile information
                  </h2>

                  <p className="mt-1 text-sm text-copy-muted">
                    Update the name shown
                    throughout TempoAI.
                  </p>
                </div>
              </div>

              <form
                className="mt-7"
                onSubmit={
                  handleProfileSubmit
                }
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
                      required
                      type="text"
                      value={
                        displayName
                      }
                      onChange={(
                        event,
                      ) => {
                        setDisplayName(
                          event.target
                            .value,
                        );
                        setProfileError(
                          "",
                        );
                        setProfileSuccess(
                          "",
                        );
                      }}
                    />
                  </div>
                </label>

                {profileError && (
                  <div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-400/20 bg-red-400/5 p-4">
                    <CircleAlert
                      className="mt-0.5 shrink-0 text-red-300"
                      size={18}
                    />

                    <p className="text-sm leading-6 text-red-200">
                      {profileError}
                    </p>
                  </div>
                )}

                {profileSuccess && (
                  <div className="mt-4 flex items-start gap-3 rounded-2xl border border-lime-soft/20 bg-lime-soft/5 p-4">
                    <CheckCircle2
                      className="mt-0.5 shrink-0 text-lime-soft"
                      size={18}
                    />

                    <p className="text-sm leading-6 text-lime-bright">
                      {
                        profileSuccess
                      }
                    </p>
                  </div>
                )}

                <Button
                  className="mt-5"
                  disabled={
                    isSavingProfile
                  }
                  type="submit"
                >
                  {isSavingProfile ? (
                    <>
                      <LoaderCircle
                        className="animate-spin"
                        size={17}
                      />
                      Saving changes
                    </>
                  ) : (
                    <>
                      <Save
                        size={17}
                      />
                      Save display name
                    </>
                  )}
                </Button>
              </form>
            </section>

            <section className="rounded-panel border border-white/10 bg-surface-raised p-6 shadow-panel sm:p-8">
              <div className="flex items-center gap-3">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                  <KeyRound
                    size={20}
                  />
                </div>

                <div>
                  <h2 className="font-display text-xl font-semibold text-white">
                    Change password
                  </h2>

                  <p className="mt-1 text-sm text-copy-muted">
                    Confirm your current
                    password before choosing
                    a new one.
                  </p>
                </div>
              </div>

              <form
                className="mt-7 space-y-5"
                onSubmit={
                  handlePasswordSubmit
                }
              >
                <label className="block">
                  <span className="text-sm font-semibold text-white">
                    Current password
                  </span>

                  <div className="relative mt-2">
                    <KeyRound
                      className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                      size={18}
                    />

                    <input
                      autoComplete="current-password"
                      className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-20 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                      name="currentPassword"
                      placeholder="Enter current password"
                      required
                      type={
                        showCurrentPassword
                          ? "text"
                          : "password"
                      }
                      value={
                        currentPassword
                      }
                      onChange={(
                        event,
                      ) => {
                        setCurrentPassword(
                          event.target
                            .value,
                        );
                        setPasswordError(
                          "",
                        );
                        setPasswordSuccess(
                          "",
                        );
                      }}
                    />

                    <button
                      aria-label={
                        showCurrentPassword
                          ? "Hide current password"
                          : "Show current password"
                      }
                      className="absolute right-4 top-1/2 flex -translate-y-1/2 items-center gap-1.5 text-xs font-medium text-copy-muted transition hover:text-white"
                      type="button"
                      onClick={() =>
                        setShowCurrentPassword(
                          (
                            currentValue,
                          ) =>
                            !currentValue,
                        )
                      }
                    >
                      {showCurrentPassword ? (
                        <EyeOff
                          size={16}
                        />
                      ) : (
                        <Eye
                          size={16}
                        />
                      )}

                      {showCurrentPassword
                        ? "Hide"
                        : "Show"}
                    </button>
                  </div>
                </label>

                <label className="block">
                  <span className="text-sm font-semibold text-white">
                    New password
                  </span>

                  <div className="relative mt-2">
                    <KeyRound
                      className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                      size={18}
                    />

                    <input
                      autoComplete="new-password"
                      className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-20 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                      maxLength={128}
                      minLength={12}
                      name="newPassword"
                      placeholder="At least 12 characters"
                      required
                      type={
                        showNewPassword
                          ? "text"
                          : "password"
                      }
                      value={
                        newPassword
                      }
                      onChange={(
                        event,
                      ) => {
                        setNewPassword(
                          event.target
                            .value,
                        );
                        setPasswordError(
                          "",
                        );
                        setPasswordSuccess(
                          "",
                        );
                      }}
                    />

                    <button
                      aria-label={
                        showNewPassword
                          ? "Hide new password"
                          : "Show new password"
                      }
                      className="absolute right-4 top-1/2 flex -translate-y-1/2 items-center gap-1.5 text-xs font-medium text-copy-muted transition hover:text-white"
                      type="button"
                      onClick={() =>
                        setShowNewPassword(
                          (
                            currentValue,
                          ) =>
                            !currentValue,
                        )
                      }
                    >
                      {showNewPassword ? (
                        <EyeOff
                          size={16}
                        />
                      ) : (
                        <Eye
                          size={16}
                        />
                      )}

                      {showNewPassword
                        ? "Hide"
                        : "Show"}
                    </button>
                  </div>

                  <p className="mt-2 text-xs leading-5 text-copy-subtle">
                    Use at least 12
                    characters. A memorable
                    passphrase works well.
                  </p>
                </label>

                <label className="block">
                  <span className="text-sm font-semibold text-white">
                    Confirm new password
                  </span>

                  <div className="relative mt-2">
                    <KeyRound
                      className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-copy-subtle"
                      size={18}
                    />

                    <input
                      autoComplete="new-password"
                      className="min-h-12 w-full rounded-2xl border border-white/10 bg-black/20 py-3 pl-11 pr-20 text-sm text-white outline-none transition placeholder:text-copy-subtle focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                      maxLength={128}
                      minLength={12}
                      name="confirmPassword"
                      placeholder="Enter new password again"
                      required
                      type={
                        showConfirmPassword
                          ? "text"
                          : "password"
                      }
                      value={
                        confirmPassword
                      }
                      onChange={(
                        event,
                      ) => {
                        setConfirmPassword(
                          event.target
                            .value,
                        );
                        setPasswordError(
                          "",
                        );
                        setPasswordSuccess(
                          "",
                        );
                      }}
                    />

                    <button
                      aria-label={
                        showConfirmPassword
                          ? "Hide confirmed password"
                          : "Show confirmed password"
                      }
                      className="absolute right-4 top-1/2 flex -translate-y-1/2 items-center gap-1.5 text-xs font-medium text-copy-muted transition hover:text-white"
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(
                          (
                            currentValue,
                          ) =>
                            !currentValue,
                        )
                      }
                    >
                      {showConfirmPassword ? (
                        <EyeOff
                          size={16}
                        />
                      ) : (
                        <Eye
                          size={16}
                        />
                      )}

                      {showConfirmPassword
                        ? "Hide"
                        : "Show"}
                    </button>
                  </div>
                </label>

                {passwordError && (
                  <div className="flex items-start gap-3 rounded-2xl border border-red-400/20 bg-red-400/5 p-4">
                    <CircleAlert
                      className="mt-0.5 shrink-0 text-red-300"
                      size={18}
                    />

                    <p className="text-sm leading-6 text-red-200">
                      {passwordError}
                    </p>
                  </div>
                )}

                {passwordSuccess && (
                  <div className="flex items-start gap-3 rounded-2xl border border-lime-soft/20 bg-lime-soft/5 p-4">
                    <CheckCircle2
                      className="mt-0.5 shrink-0 text-lime-soft"
                      size={18}
                    />

                    <p className="text-sm leading-6 text-lime-bright">
                      {
                        passwordSuccess
                      }
                    </p>
                  </div>
                )}

                <Button
                  disabled={
                    isChangingPassword
                  }
                  type="submit"
                >
                  {isChangingPassword ? (
                    <>
                      <LoaderCircle
                        className="animate-spin"
                        size={17}
                      />
                      Changing password
                    </>
                  ) : (
                    <>
                      <KeyRound
                        size={17}
                      />
                      Change password
                    </>
                  )}
                </Button>
              </form>
            </section>
          </div>

          <aside className="h-fit rounded-panel border border-white/10 bg-surface-raised p-6 shadow-panel sm:p-8">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
              <ShieldCheck
                size={20}
              />
            </div>

            <h2 className="mt-5 font-display text-xl font-semibold text-white">
              Account details
            </h2>

            <p className="mt-3 text-sm leading-6 text-copy-muted">
              Your email address is used
              for sign-in and cannot
              currently be changed.
            </p>

            <div className="mt-6 grid gap-4">
              <ProfileDetail
                icon={
                  <Mail
                    size={18}
                  />
                }
                label="Email address"
                value={user.email}
              />

              <ProfileDetail
                icon={
                  <CalendarDays
                    size={18}
                  />
                }
                label="Account created"
                value={formatAccountDate(
                  user.createdAt,
                )}
              />

              <ProfileDetail
                icon={
                  <ShieldCheck
                    size={18}
                  />
                }
                label="Session security"
                value="Secure server session"
              />
            </div>

            <div className="mt-7 border-t border-white/10 pt-6">
              <h3 className="text-sm font-semibold text-white">
                Sign out of TempoAI
              </h3>

              <p className="mt-2 text-sm leading-6 text-copy-muted">
                This invalidates your
                current session on the
                server.
              </p>

              {logoutError && (
                <p className="mt-4 rounded-xl border border-red-400/20 bg-red-400/5 p-3 text-sm text-red-200">
                  {logoutError}
                </p>
              )}

              <Button
                className="mt-5 w-full"
                disabled={
                  isLoggingOut
                }
                type="button"
                variant="secondary"
                onClick={
                  handleLogout
                }
              >
                <LogOut
                  size={17}
                />

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