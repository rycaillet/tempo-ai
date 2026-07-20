import { useRef, useState, type ChangeEvent } from "react";
import {
  CheckCircle2,
  FileVideo2,
  RotateCcw,
  UploadCloud,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import Button from "../ui/Button";
import Panel from "../ui/Panel";

const allowedVideoTypes = ["video/mp4", "video/quicktime", "video/webm"];
const maximumFileSize = 250 * 1024 * 1024;

function formatFileSize(bytes: number) {
  const megabytes = bytes / (1024 * 1024);
  return `${megabytes.toFixed(1)} MB`;
}

function UploadDropzone() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function validateAndSelectFile(file: File) {
    setError("");

    if (!allowedVideoTypes.includes(file.type)) {
      setSelectedFile(null);
      setError("Choose an MP4, MOV, or WEBM video.");
      return;
    }

    if (file.size > maximumFileSize) {
      setSelectedFile(null);
      setError("The selected video must be smaller than 250 MB.");
      return;
    }

    setSelectedFile(file);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (file) {
      validateAndSelectFile(file);
    }
  }

  function removeSelectedFile() {
    setSelectedFile(null);
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function startAnalysis() {
    if (!selectedFile) {
      setError("Select a golf swing video before starting the analysis.");
      return;
    }

    navigate("/analysis/processing");
  }

  return (
    <Panel
      className="border-2 border-dashed border-lime-soft/25"
      variant="raised"
    >
      <input
        ref={fileInputRef}
        accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
        className="hidden"
        onChange={handleFileChange}
        type="file"
      />

      {!selectedFile ? (
        <div className="flex flex-col items-center py-14 text-center">
          <div className="rounded-full bg-lime-soft/10 p-6 text-lime-soft">
            <UploadCloud size={54} />
          </div>

          <h2 className="mt-8 font-display text-3xl font-semibold text-white">
            Choose your swing video
          </h2>

          <p className="mt-3 max-w-md leading-7 text-copy-muted">
            Upload one golf swing and TempoAI will analyze your mechanics,
            tempo, posture, and movement patterns.
          </p>

          <Button className="mt-10" onClick={openFilePicker} size="lg">
            Choose video
          </Button>

          <p className="mt-6 text-sm text-copy-subtle">
            MP4, MOV, or WEBM · Maximum file size: 250 MB
          </p>
        </div>
      ) : (
        <div className="py-10">
          <div className="mx-auto flex max-w-xl flex-col items-center text-center">
            <div className="flex size-16 items-center justify-center rounded-full bg-lime-soft/10 text-lime-soft">
              <CheckCircle2 size={32} />
            </div>

            <p className="mt-7 text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
              Video ready
            </p>

            <h2 className="mt-3 font-display text-3xl font-semibold text-white">
              Ready for analysis
            </h2>

            <div className="mt-8 flex w-full items-center gap-4 rounded-2xl border border-white/10 bg-black/20 p-4 text-left">
              <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-white/5 text-ice">
                <FileVideo2 size={23} />
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-white">
                  {selectedFile.name}
                </p>

                <p className="mt-1 text-sm text-copy-subtle">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>

              <button
                aria-label="Choose a different video"
                className="rounded-full p-2 text-copy-muted transition hover:bg-white/5 hover:text-white"
                onClick={removeSelectedFile}
                type="button"
              >
                <RotateCcw size={19} />
              </button>
            </div>

            <div className="mt-8 flex w-full flex-col gap-3 sm:flex-row">
              <Button
                className="flex-1"
                onClick={openFilePicker}
                variant="secondary"
              >
                Replace video
              </Button>

              <Button
                className="flex-1"
                onClick={startAnalysis}
              >
                Analyze swing
              </Button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-5 text-center text-sm font-medium text-danger">
          {error}
        </p>
      )}
    </Panel>
  );
}

export default UploadDropzone;