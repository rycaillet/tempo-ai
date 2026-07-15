import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#07110d] px-6 text-center text-white">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#84ff4d]">
          Error 404
        </p>

        <h1 className="mt-5 text-6xl font-semibold tracking-[-0.06em]">
          Page not found.
        </h1>

        <p className="mx-auto mt-5 max-w-md text-slate-400">
          The page you were looking for does not exist or may have moved.
        </p>

        <Link
          to="/"
          className="mt-9 inline-flex items-center gap-2 rounded-full bg-[#84ff4d] px-6 py-3 font-semibold text-[#07110d]"
        >
          <ArrowLeft size={18} />
          Return home
        </Link>
      </div>
    </main>
  );
}

export default NotFoundPage;