import type { SwingAnalysis } from "../types/analysis";

export const demoAnalysis: SwingAnalysis = {
  summary: {
    id: "demo-swing",
    title: "Range Session",
    club: "7 Iron",
    cameraAngle: "Down the line",
    date: "July 20, 2026",
    overallScore: 84,
    change: "+6 from your previous analysis",
    summary:
      "Your posture and finish balance improved significantly. The highest-priority opportunity is maintaining hip depth during the downswing so you can rotate through impact more consistently.",
    strength:
      "Your finish position was balanced and your upper-body rotation remained controlled.",
  },

  phases: [
    {
      id: "address",
      label: "Address",
      timestamp: "0.0s",
      status: "complete",
    },
    {
      id: "takeaway",
      label: "Takeaway",
      timestamp: "0.6s",
      status: "complete",
    },
    {
      id: "top",
      label: "Top",
      timestamp: "1.2s",
      status: "complete",
    },
    {
      id: "downswing",
      label: "Downswing",
      timestamp: "1.5s",
      status: "complete",
    },
    {
      id: "impact",
      label: "Impact",
      timestamp: "1.7s",
      status: "active",
    },
    {
      id: "finish",
      label: "Finish",
      timestamp: "2.4s",
      status: "complete",
    },
  ],

  metrics: [
    {
      id: "setup",
      label: "Setup",
      score: 88,
      description: "Athletic posture and stable lower body.",
    },
    {
      id: "rotation",
      label: "Rotation",
      score: 82,
      description: "Good shoulder turn with room for more hip depth.",
    },
    {
      id: "tempo",
      label: "Tempo",
      score: 79,
      description: "Slightly fast transition from the top.",
    },
    {
      id: "stability",
      label: "Stability",
      score: 86,
      description: "Controlled head movement and solid balance.",
    },
    {
      id: "finish",
      label: "Finish",
      score: 91,
      description: "Balanced finish with full body rotation.",
    },
  ],

  findings: [
    {
      id: "finding-1",
      priority: 1,
      title: "Maintain hip depth through impact",
      phase: "Downswing",
      severity: "High",
      evidence:
        "Hip position moved approximately 9% toward the ball before impact.",
      explanation:
        "Your hips move closer to the ball during the downswing, which can reduce space for your arms and make contact less predictable.",
      drill: {
        name: "Wall Touch Drill",
        instructions:
          "Make slow practice swings while keeping your trail hip in contact with a wall during the backswing and your lead hip touching the wall through impact.",
      },
    },
    {
      id: "finding-2",
      priority: 2,
      title: "Smooth the transition",
      phase: "Top",
      severity: "Medium",
      evidence:
        "Measured tempo ratio was 2.6:1 compared with the 3:1 target.",
      explanation:
        "Your downswing begins slightly quickly, which can make it harder to sequence your lower and upper body consistently.",
      drill: {
        name: "Pause-at-the-Top Drill",
        instructions:
          "Make three-quarter swings and pause briefly at the top before beginning the downswing.",
      },
    },
    {
      id: "finding-3",
      priority: 3,
      title: "Preserve spine angle",
      phase: "Impact",
      severity: "Low",
      evidence: "Spine inclination changed by approximately 5 degrees.",
      explanation:
        "Your posture remains generally strong, but preserving your address inclination a little longer may improve contact consistency.",
      drill: {
        name: "Chair Posture Drill",
        instructions:
          "Set a chair behind your hips and rehearse turning while maintaining light contact throughout the swing.",
      },
    },
  ],

  practicePlan: [
    {
      label: "Warm-up",
      duration: "5 minutes",
      instructions:
        "Make slow-motion turns while maintaining your address posture.",
    },
    {
      label: "Primary drill",
      duration: "10 minutes",
      instructions:
        "Complete 15 wall-touch rehearsals followed by five half-speed shots.",
    },
    {
      label: "Tempo work",
      duration: "5 minutes",
      instructions: "Hit five balls using the pause-at-the-top drill.",
    },
    {
      label: "Recording checkpoint",
      duration: "Final 5 swings",
      instructions:
        "Record five down-the-line swings from the same camera position for comparison.",
    },
  ],
};