import { Activity, BrainCircuit, ScanLine } from "lucide-react";

const features = [
  {
    title: "Pose Tracking",
    description: "Track key body positions throughout every phase of your swing.",
    icon: ScanLine,
  },
  {
    title: "Swing Metrics",
    description: "Measure posture, movement, tempo, rotation, and balance.",
    icon: Activity,
  },
  {
    title: "AI Coaching",
    description: "Turn measurable swing data into focused feedback and drills.",
    icon: BrainCircuit,
  },
];

function App() {
  return (
    <main className="min-h-screen bg-[#07110d] px-6 py-16 text-slate-100">
      <section className="mx-auto max-w-6xl">
        <div className="inline-flex items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm font-medium text-emerald-300">
          AI-powered golf swing analysis
        </div>

        <h1 className="mt-8 max-w-4xl text-5xl font-semibold tracking-tight sm:text-7xl">
          Smarter swing feedback from every frame.
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">
          TempoAI combines computer vision, swing measurements, and generative
          AI to provide clear, personalized golf coaching.
        </p>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {features.map(({ title, description, icon: Icon }) => (
            <article
              key={title}
              className="rounded-3xl border border-white/10 bg-white/5 p-6"
            >
              <div className="flex size-12 items-center justify-center rounded-2xl bg-emerald-400/10 text-emerald-300">
                <Icon size={24} />
              </div>

              <h2 className="mt-6 text-xl font-semibold">{title}</h2>

              <p className="mt-3 leading-7 text-slate-400">{description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;
