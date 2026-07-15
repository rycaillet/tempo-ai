import { useParams } from "react-router-dom";

import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import PageHeader from "../components/ui/PageHeader";
import Section from "../components/ui/Section";

function AnalysisPage() {
  const { swingId } = useParams();

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container>
          <PageHeader
            eyebrow="Swing analysis"
            title="Analysis results"
            description={`Detailed results for ${swingId ?? "this swing"} will appear here.`}
          />

          <Button className="mt-10" to="/dashboard" variant="secondary">
            Return to dashboard
          </Button>
        </Container>
      </Section>
    </main>
  );
}

export default AnalysisPage;