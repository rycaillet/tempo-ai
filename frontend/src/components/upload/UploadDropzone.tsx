import { UploadCloud } from "lucide-react";

import Button from "../ui/Button";
import Panel from "../ui/Panel";

function UploadDropzone() {
  return (
    <Panel
      variant="raised"
      className="border-2 border-dashed border-lime-soft/25"
    >
      <div className="flex flex-col items-center py-14 text-center">
        <div className="rounded-full bg-lime-soft/10 p-6">
          <UploadCloud
            size={54}
            className="text-lime-soft"
          />
        </div>

        <h2 className="mt-8 font-display text-3xl font-semibold text-white">
          Drag your swing video here
        </h2>

        <p className="mt-3 max-w-md leading-7 text-copy-muted">
          Upload one golf swing and TempoAI will analyze your mechanics,
          tempo, posture, and movement patterns.
        </p>

        <Button
          className="mt-10"
          size="lg"
        >
          Choose Video
        </Button>

        <p className="mt-6 text-sm text-copy-subtle">
          Maximum file size: 250 MB
        </p>
      </div>
    </Panel>
  );
}

export default UploadDropzone;