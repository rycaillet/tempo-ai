import { LoaderCircle } from "lucide-react";

function AuthLoadingScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6 text-copy">
      <div className="text-center">
        <LoaderCircle
          className="mx-auto animate-spin text-lime-soft"
          size={32}
        />

        <p className="mt-4 text-sm text-copy-muted">
          Restoring your TempoAI session
        </p>
      </div>
    </main>
  );
}

export default AuthLoadingScreen;