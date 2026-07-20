import Container from "../ui/Container";
import Panel from "../ui/Panel";
import Section from "../ui/Section";

function SkeletonBlock({
  className = "",
}: {
  className?: string;
}) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-xl bg-white/[0.07] ${className}`}
    />
  );
}

function AnalysisSkeleton() {
  return (
    <main
      aria-busy="true"
      aria-label="Loading swing analysis"
      className="min-h-screen bg-canvas text-copy"
    >
      <Section spacing="lg">
        <Container size="wide">
          <SkeletonBlock className="h-5 w-40" />

          <div className="mt-10 flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div className="w-full max-w-2xl">
              <SkeletonBlock className="h-4 w-36" />
              <SkeletonBlock className="mt-5 h-14 w-full max-w-md" />

              <div className="mt-5 flex flex-wrap gap-3">
                <SkeletonBlock className="h-5 w-20" />
                <SkeletonBlock className="h-5 w-32" />
                <SkeletonBlock className="h-5 w-36" />
              </div>
            </div>

            <div className="flex gap-3">
              <SkeletonBlock className="h-11 w-40 rounded-button" />
              <SkeletonBlock className="h-11 w-36 rounded-button" />
            </div>
          </div>

          <div className="mt-14 grid gap-6 xl:grid-cols-[1.55fr_0.65fr]">
            <Panel padding="none" variant="raised">
              <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
                <div>
                  <SkeletonBlock className="h-6 w-44" />
                  <SkeletonBlock className="mt-3 h-4 w-32" />
                </div>

                <SkeletonBlock className="h-7 w-32 rounded-full" />
              </div>

              <div className="aspect-video p-8">
                <SkeletonBlock className="h-full w-full rounded-panel" />
              </div>
            </Panel>

            <Panel
              className="flex min-h-80 items-center justify-center"
              padding="lg"
              variant="raised"
            >
              <div className="flex flex-col items-center">
                <SkeletonBlock className="size-48 rounded-full" />
                <SkeletonBlock className="mt-6 h-5 w-28" />
                <SkeletonBlock className="mt-3 h-4 w-40" />
              </div>
            </Panel>
          </div>

          <div className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <Panel key={index} padding="md" variant="raised">
                <div className="flex items-center justify-between">
                  <SkeletonBlock className="h-4 w-20" />
                  <SkeletonBlock className="size-5 rounded-full" />
                </div>

                <SkeletonBlock className="mt-6 h-11 w-16" />
                <SkeletonBlock className="mt-5 h-2 w-full rounded-full" />
                <SkeletonBlock className="mt-5 h-4 w-full" />
                <SkeletonBlock className="mt-2 h-4 w-3/4" />
              </Panel>
            ))}
          </div>

          <div className="mt-16 grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
            <div className="space-y-6">
              <Panel padding="lg" variant="raised">
                <div className="flex gap-4">
                  <SkeletonBlock className="size-12 shrink-0 rounded-2xl" />

                  <div className="flex-1">
                    <SkeletonBlock className="h-4 w-40" />
                    <SkeletonBlock className="mt-4 h-9 w-3/4" />
                    <SkeletonBlock className="mt-6 h-4 w-full" />
                    <SkeletonBlock className="mt-3 h-4 w-full" />
                    <SkeletonBlock className="mt-3 h-4 w-5/6" />
                    <SkeletonBlock className="mt-7 h-24 w-full rounded-2xl" />
                  </div>
                </div>
              </Panel>

              <div>
                <SkeletonBlock className="h-4 w-40" />
                <SkeletonBlock className="mt-4 h-9 w-72" />

                <div className="mt-6 space-y-4">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <Panel key={index} padding="lg" variant="raised">
                      <div className="flex gap-5">
                        <SkeletonBlock className="size-12 shrink-0 rounded-full" />

                        <div className="flex-1">
                          <SkeletonBlock className="h-7 w-2/3" />
                          <SkeletonBlock className="mt-4 h-4 w-28" />
                          <SkeletonBlock className="mt-6 h-4 w-full" />
                          <SkeletonBlock className="mt-3 h-4 w-5/6" />
                          <SkeletonBlock className="mt-7 h-20 w-full" />
                        </div>
                      </div>
                    </Panel>
                  ))}
                </div>
              </div>
            </div>

            <Panel className="h-fit" padding="lg" variant="raised">
              <div className="flex gap-3">
                <SkeletonBlock className="size-11 rounded-2xl" />

                <div className="flex-1">
                  <SkeletonBlock className="h-4 w-28" />
                  <SkeletonBlock className="mt-3 h-7 w-48" />
                </div>
              </div>

              <div className="mt-8 space-y-7">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="flex gap-4">
                    <SkeletonBlock className="size-9 shrink-0 rounded-full" />

                    <div className="flex-1">
                      <SkeletonBlock className="h-5 w-32" />
                      <SkeletonBlock className="mt-3 h-4 w-full" />
                      <SkeletonBlock className="mt-2 h-4 w-4/5" />
                    </div>
                  </div>
                ))}
              </div>

              <SkeletonBlock className="mt-8 h-11 w-full rounded-button" />
            </Panel>
          </div>
        </Container>
      </Section>
    </main>
  );
}

export default AnalysisSkeleton;