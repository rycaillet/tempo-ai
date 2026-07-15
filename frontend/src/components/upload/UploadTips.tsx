function UploadTips() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-display text-xl font-semibold text-white">
          Best Recording Tips
        </h3>

        <p className="mt-2 text-copy-muted">
          Following these tips helps TempoAI produce more accurate swing
          analysis.
        </p>
      </div>

      <div className="space-y-4 text-sm text-copy-muted">
        <div>
          <span className="font-semibold text-white">✓ One golfer only</span>
          <p className="mt-1">
            Make sure only one golfer is visible in the frame.
          </p>
        </div>

        <div>
          <span className="font-semibold text-white">✓ Stable camera</span>
          <p className="mt-1">
            Rest your phone on a tripod or golf bag whenever possible.
          </p>
        </div>

        <div>
          <span className="font-semibold text-white">✓ Camera angle</span>
          <p className="mt-1">
            Down-the-line or face-on provides the most accurate analysis.
          </p>
        </div>

        <div>
          <span className="font-semibold text-white">✓ File Types</span>
          <p className="mt-1">
            MP4 • MOV • WEBM
          </p>
        </div>
      </div>
    </div>
  );
}

export default UploadTips;