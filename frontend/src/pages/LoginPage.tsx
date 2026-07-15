import { Link } from "react-router-dom";

function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#07110d] px-6 text-white">
      <div className="w-full max-w-md">
        <Link
          to="/"
          className="text-xl font-semibold tracking-[-0.04em]"
        >
          Tempo<span className="text-[#84ff4d]">AI</span>
        </Link>

        <h1 className="mt-10 text-4xl font-semibold tracking-[-0.04em]">
          Welcome back
        </h1>

        <p className="mt-3 text-slate-400">
          Login functionality will be added during the authentication
          milestone.
        </p>

        <Link
          to="/register"
          className="mt-8 inline-block text-sm font-semibold text-[#84ff4d]"
        >
          Create an account
        </Link>
      </div>
    </main>
  );
}

export default LoginPage;