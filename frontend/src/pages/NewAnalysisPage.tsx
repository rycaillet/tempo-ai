import Container from "../components/ui/Container";
import PageHeader from "../components/ui/PageHeader";
import Section from "../components/ui/Section";
import UploadDropzone from "../components/upload/UploadDropzone";
import UploadTips from "../components/upload/UploadTips";

function NewAnalysisPage() {
  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="wide">
          <PageHeader
            eyebrow="New Analysis"
            title="Upload your golf swing"
            description="Record one swing, upload your video, and receive AI-powered coaching feedback in seconds."
          />

          <div className="mt-14 grid gap-10 lg:grid-cols-[1.4fr_0.6fr]">
            <UploadDropzone />

            <UploadTips />
          </div>
        </Container>
      </Section>
    </main>
  );
}

export default NewAnalysisPage;