import type { PoseVariant } from "../../types/analysis";

type SwingPoseOverlayProps = {
  variant: PoseVariant;
};

type PoseLine = {
  className: string;
};

type PoseConfiguration = {
  head: string;
  torso: string;
  leadArm: string;
  trailArm: string;
  leadLeg: string;
  trailLeg: string;
  club: string;
};

const poses: Record<PoseVariant, PoseConfiguration> = {
  address: {
    head: "left-[48%] top-[15%]",
    torso: "left-[49%] top-[25%] h-[40%] rotate-6",
    leadArm: "left-[42%] top-[36%] w-[17%] rotate-[28deg]",
    trailArm: "left-[49%] top-[37%] w-[17%] rotate-[40deg]",
    leadLeg: "left-[44%] top-[63%] h-[25%] rotate-[10deg]",
    trailLeg: "left-[55%] top-[63%] h-[25%] -rotate-[10deg]",
    club: "left-[58%] top-[45%] w-[25%] rotate-[58deg]",
  },

  takeaway: {
    head: "left-[48%] top-[15%]",
    torso: "left-[49%] top-[25%] h-[40%] rotate-3",
    leadArm: "left-[38%] top-[34%] w-[21%] rotate-[5deg]",
    trailArm: "left-[46%] top-[33%] w-[18%] rotate-[18deg]",
    leadLeg: "left-[44%] top-[63%] h-[25%] rotate-[9deg]",
    trailLeg: "left-[55%] top-[63%] h-[25%] -rotate-[9deg]",
    club: "left-[26%] top-[31%] w-[31%] -rotate-[4deg]",
  },

  top: {
    head: "left-[48%] top-[15%]",
    torso: "left-[49%] top-[25%] h-[40%] -rotate-3",
    leadArm: "left-[38%] top-[29%] w-[21%] -rotate-[35deg]",
    trailArm: "left-[48%] top-[25%] w-[17%] -rotate-[55deg]",
    leadLeg: "left-[44%] top-[63%] h-[25%] rotate-[7deg]",
    trailLeg: "left-[55%] top-[63%] h-[25%] -rotate-[7deg]",
    club: "left-[28%] top-[17%] w-[35%] rotate-[5deg]",
  },

  downswing: {
    head: "left-[48%] top-[15%]",
    torso: "left-[49%] top-[25%] h-[40%] rotate-3",
    leadArm: "left-[42%] top-[34%] w-[20%] rotate-[30deg]",
    trailArm: "left-[49%] top-[34%] w-[17%] rotate-[48deg]",
    leadLeg: "left-[44%] top-[63%] h-[25%] rotate-[5deg]",
    trailLeg: "left-[56%] top-[63%] h-[25%] -rotate-[13deg]",
    club: "left-[57%] top-[45%] w-[29%] rotate-[60deg]",
  },

  impact: {
    head: "left-[47%] top-[15%]",
    torso: "left-[49%] top-[25%] h-[40%] rotate-6",
    leadArm: "left-[42%] top-[36%] w-[21%] rotate-[34deg]",
    trailArm: "left-[50%] top-[38%] w-[17%] rotate-[49deg]",
    leadLeg: "left-[43%] top-[63%] h-[25%] rotate-[2deg]",
    trailLeg: "left-[56%] top-[63%] h-[25%] -rotate-[18deg]",
    club: "left-[60%] top-[48%] w-[27%] rotate-[65deg]",
  },

  finish: {
    head: "left-[48%] top-[15%]",
    torso: "left-[49%] top-[25%] h-[40%] -rotate-6",
    leadArm: "left-[43%] top-[31%] w-[20%] -rotate-[42deg]",
    trailArm: "left-[49%] top-[29%] w-[18%] -rotate-[58deg]",
    leadLeg: "left-[45%] top-[63%] h-[25%] rotate-[2deg]",
    trailLeg: "left-[55%] top-[63%] h-[23%] rotate-[20deg]",
    club: "left-[33%] top-[18%] w-[34%] rotate-[20deg]",
  },
};

function PoseLine({ className }: PoseLine) {
  return (
    <div
      className={[
        "absolute h-[3px] origin-left rounded-full",
        "bg-lime-soft shadow-[0_0_18px_rgba(132,255,77,0.55)]",
        "transition-all duration-500 ease-out",
        className,
      ].join(" ")}
    />
  );
}

function SwingPoseOverlay({ variant }: SwingPoseOverlayProps) {
  const pose = poses[variant];

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 transition-all duration-500"
    >
      <div
        className={[
          "absolute size-10 rounded-full border-2 border-lime-soft",
          "shadow-[0_0_24px_rgba(132,255,77,0.55)]",
          "transition-all duration-500 ease-out",
          pose.head,
        ].join(" ")}
      />

      <div
        className={[
          "absolute w-[3px] origin-top rounded-full",
          "bg-lime-soft shadow-[0_0_18px_rgba(132,255,77,0.55)]",
          "transition-all duration-500 ease-out",
          pose.torso,
        ].join(" ")}
      />

      <PoseLine className={pose.leadArm} />
      <PoseLine className={pose.trailArm} />

      <div
        className={[
          "absolute w-[3px] origin-top rounded-full",
          "bg-lime-soft shadow-[0_0_18px_rgba(132,255,77,0.55)]",
          "transition-all duration-500 ease-out",
          pose.leadLeg,
        ].join(" ")}
      />

      <div
        className={[
          "absolute w-[3px] origin-top rounded-full",
          "bg-lime-soft shadow-[0_0_18px_rgba(132,255,77,0.55)]",
          "transition-all duration-500 ease-out",
          pose.trailLeg,
        ].join(" ")}
      />

      <div
        className={[
          "absolute h-[2px] origin-left rounded-full",
          "bg-ice shadow-[0_0_16px_rgba(115,215,255,0.5)]",
          "transition-all duration-500 ease-out",
          pose.club,
        ].join(" ")}
      />
    </div>
  );
}

export default SwingPoseOverlay;