import {
  BarChart3,
  GitCompareArrows,
  History,
  LogOut,
  Menu,
  PlusCircle,
  UserRound,
  X,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  NavLink,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

type AppShellProps = {
  children: ReactNode;
};

const navigationItems = [
  {
    label: "Dashboard",
    to: "/dashboard",
    icon: BarChart3,
  },
  {
    label: "New Analysis",
    to: "/analysis/new",
    icon: PlusCircle,
  },
  {
    label: "History",
    to: "/history",
    icon: History,
  },
  {
    label: "Compare",
    to: "/compare",
    icon: GitCompareArrows,
  },
  {
    label: "Profile",
    to: "/profile",
    icon: UserRound,
  },
];

function buildNavigationClassName({
  isActive,
}: {
  isActive: boolean;
}) {
  return [
    "inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition",
    isActive
      ? "bg-lime-soft/12 text-lime-soft"
      : "text-copy-muted hover:bg-white/5 hover:text-white",
  ].join(" ");
}

function AppShell({
  children,
}: AppShellProps) {
  const navigate = useNavigate();

  const {
    user,
    logout,
  } = useAuth();

  const menuButtonRef =
    useRef<HTMLButtonElement | null>(null);

  const mobileMenuRef =
    useRef<HTMLDivElement | null>(null);

  const [isMenuOpen, setIsMenuOpen] =
    useState(false);

  const [isLoggingOut, setIsLoggingOut] =
    useState(false);

  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    function handlePointerDown(
      event: MouseEvent | TouchEvent,
    ) {
      const target = event.target;

      if (!(target instanceof Node)) {
        return;
      }

      const clickedMenu =
        mobileMenuRef.current?.contains(
          target,
        ) ?? false;

      const clickedMenuButton =
        menuButtonRef.current?.contains(
          target,
        ) ?? false;

      if (
        !clickedMenu &&
        !clickedMenuButton
      ) {
        setIsMenuOpen(false);
      }
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    }

    document.addEventListener(
      "mousedown",
      handlePointerDown,
    );

    document.addEventListener(
      "touchstart",
      handlePointerDown,
    );

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handlePointerDown,
      );

      document.removeEventListener(
        "touchstart",
        handlePointerDown,
      );

      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [isMenuOpen]);

  async function handleLogout() {
    if (isLoggingOut) {
      return;
    }

    try {
      setIsLoggingOut(true);

      await logout();

      navigate("/login", {
        replace: true,
      });
    } finally {
      setIsLoggingOut(false);
      setIsMenuOpen(false);
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-copy">
      <header className="sticky top-0 z-50 border-b border-white/10 bg-canvas/90 backdrop-blur-xl">
        <div className="mx-auto flex min-h-18 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <NavLink
            className="shrink-0 font-display text-2xl font-semibold tracking-[-0.05em] text-white"
            to="/dashboard"
            onClick={() =>
              setIsMenuOpen(false)
            }
          >
            Tempo
            <span className="text-lime-soft">
              AI
            </span>
          </NavLink>

          <nav className="hidden items-center gap-1 xl:flex">
            {navigationItems.map(
              ({
                label,
                to,
                icon: Icon,
              }) => (
                <NavLink
                  key={to}
                  className={
                    buildNavigationClassName
                  }
                  to={to}
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              ),
            )}
          </nav>

          <div className="hidden items-center gap-3 xl:flex">
            <div className="max-w-44 text-right">
              <p className="truncate text-sm font-semibold text-white">
                {user?.displayName}
              </p>

              <p className="truncate text-xs text-copy-subtle">
                {user?.email}
              </p>
            </div>

            <button
              aria-label="Sign out"
              className="flex size-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-copy-muted transition hover:border-white/20 hover:bg-white/10 hover:text-white"
              disabled={isLoggingOut}
              type="button"
              onClick={() =>
                void handleLogout()
              }
            >
              <LogOut size={17} />
            </button>
          </div>

          <button
            ref={menuButtonRef}
            aria-controls="mobile-navigation-menu"
            aria-expanded={isMenuOpen}
            aria-label={
              isMenuOpen
                ? "Close navigation menu"
                : "Open navigation menu"
            }
            className="flex size-11 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white transition hover:bg-white/10 xl:hidden"
            type="button"
            onClick={() =>
              setIsMenuOpen(
                (currentValue) =>
                  !currentValue,
              )
            }
          >
            {isMenuOpen ? (
              <X size={20} />
            ) : (
              <Menu size={20} />
            )}
          </button>
        </div>

        {isMenuOpen && (
          <div
            ref={mobileMenuRef}
            id="mobile-navigation-menu"
            className="border-t border-white/10 bg-surface-raised px-4 py-5 shadow-panel xl:hidden"
          >
            <div className="mx-auto max-w-7xl">
              <div className="mb-5 rounded-2xl border border-white/10 bg-black/10 p-4">
                <p className="font-semibold text-white">
                  {user?.displayName}
                </p>

                <p className="mt-1 text-sm text-copy-subtle">
                  {user?.email}
                </p>
              </div>

              <nav className="grid gap-2">
                {navigationItems.map(
                  ({
                    label,
                    to,
                    icon: Icon,
                  }) => (
                    <NavLink
                      key={to}
                      className={({
                        isActive,
                      }) =>
                        [
                          "flex min-h-12 items-center gap-3 rounded-2xl px-4 text-sm font-semibold transition",
                          isActive
                            ? "bg-lime-soft/12 text-lime-soft"
                            : "text-copy-muted hover:bg-white/5 hover:text-white",
                        ].join(" ")
                      }
                      to={to}
                      onClick={() =>
                        setIsMenuOpen(false)
                      }
                    >
                      <Icon size={18} />
                      {label}
                    </NavLink>
                  ),
                )}
              </nav>

              <button
                className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm font-semibold text-white transition hover:bg-white/10"
                disabled={isLoggingOut}
                type="button"
                onClick={() =>
                  void handleLogout()
                }
              >
                <LogOut size={17} />

                {isLoggingOut
                  ? "Signing out"
                  : "Sign out"}
              </button>
            </div>
          </div>
        )}
      </header>

      {children}
    </div>
  );
}

export default AppShell;