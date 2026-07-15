function DashboardPage() {
  return (
    <main className="min-h-screen bg-[#07110d] px-6 py-16 text-white">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#84ff4d]">
          Performance overview
        </p>

        <h1 className="mt-4 text-5xl font-semibold tracking-[-0.05em]">
          Dashboard
        </h1>

        <p className="mt-4 max-w-xl text-slate-400">
          Your swing activity, improvement trends, and recent coaching insights
          will appear here.
        </p>
      </div>
    </main>
  );
}

export default DashboardPage;