export type RecentSwing = {
  id: string;
  title: string;
  club: string;
  cameraAngle: string;
  date: string;
  score: number;
  status: "Complete" | "Processing";
  finding: string;
};

export const dashboardMetrics = {
  overallScore: 84,
  scoreChange: "+6 from last session",
  totalSwings: "17",
  averageTempo: "3.1:1",
  bestClub: "7 Iron",
  consistency: "82%",
};

export const recentSwings: RecentSwing[] = [
  {
    id: "swing-1",
    title: "Range Session",
    club: "7 Iron",
    cameraAngle: "Down the line",
    date: "July 15, 2026",
    score: 84,
    status: "Complete",
    finding: "Improved posture through impact",
  },
  {
    id: "swing-2",
    title: "Driver Tempo Check",
    club: "Driver",
    cameraAngle: "Face on",
    date: "July 12, 2026",
    score: 78,
    status: "Complete",
    finding: "Transition remains slightly rushed",
  },
  {
    id: "swing-3",
    title: "Backyard Practice",
    club: "Pitching Wedge",
    cameraAngle: "Down the line",
    date: "July 9, 2026",
    score: 81,
    status: "Complete",
    finding: "Strong finish balance",
  },
];