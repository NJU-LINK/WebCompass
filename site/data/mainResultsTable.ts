export type MainResultsRow = {
  model: string;
  group: "Closed-Source" | "Open-Source";
  generation: { ex: number; in: number; ae: number };
  editing: { ex: number; in: number; ae: number };
  repair: { ex: number; in: number; ae: number };
  average: { ex: number; in: number; ae: number };
};

// Main table in Paper/sec/4_experiments.tex (tab:main_results)
export const mainResultsRows: MainResultsRow[] = [
  {
    model: "Claude-Opus-4.5",
    group: "Closed-Source",
    generation: { ex: 77.18, in: 68.95, ae: 62.26 },
    editing: { ex: 71.86, in: 65.82, ae: 60.83 },
    repair: { ex: 48.45, in: 85.54, ae: 65.71 },
    average: { ex: 67.4, in: 67.4, ae: 67.4 }
  },
  {
    model: "Gemini-3-Pro-Preview",
    group: "Closed-Source",
    generation: { ex: 74.05, in: 55.76, ae: 64.07 },
    editing: { ex: 69.52, in: 65.14, ae: 58.16 },
    repair: { ex: 54.16, in: 87.3, ae: 72.0 },
    average: { ex: 66.68, in: 66.68, ae: 66.68 }
  },
  {
    model: "Gemini-3-Flash-Preview",
    group: "Closed-Source",
    generation: { ex: 74.87, in: 54.32, ae: 62.42 },
    editing: { ex: 65.95, in: 62.35, ae: 57.21 },
    repair: { ex: 53.18, in: 86.84, ae: 71.65 },
    average: { ex: 65.42, in: 65.42, ae: 65.42 }
  },
  {
    model: "GPT-5.2",
    group: "Closed-Source",
    generation: { ex: 75.38, in: 60.22, ae: 55.92 },
    editing: { ex: 66.97, in: 62.7, ae: 56.63 },
    repair: { ex: 41.24, in: 79.33, ae: 58.7 },
    average: { ex: 61.9, in: 61.9, ae: 61.9 }
  },
  {
    model: "Claude-Sonnet-4.5",
    group: "Closed-Source",
    generation: { ex: 65.3, in: 50.37, ae: 56.78 },
    editing: { ex: 60.06, in: 53.71, ae: 45.51 },
    repair: { ex: 40.44, in: 80.63, ae: 61.31 },
    average: { ex: 57.12, in: 57.12, ae: 57.12 }
  },
  {
    model: "235B-A22B-Instruct",
    group: "Open-Source",
    generation: { ex: 61.26, in: 42.14, ae: 47.06 },
    editing: { ex: 27.74, in: 25.48, ae: 23.53 },
    repair: { ex: 27.3, in: 68.87, ae: 46.88 },
    average: { ex: 41.14, in: 41.14, ae: 41.14 }
  },
  {
    model: "235B-A22B-Thinking",
    group: "Open-Source",
    generation: { ex: 63.86, in: 35.02, ae: 45.21 },
    editing: { ex: 22.15, in: 21.67, ae: 19.06 },
    repair: { ex: 27.02, in: 68.74, ae: 46.28 },
    average: { ex: 38.78, in: 38.78, ae: 38.78 }
  },
  {
    model: "32B-Instruct",
    group: "Open-Source",
    generation: { ex: 50.39, in: 25.62, ae: 34.56 },
    editing: { ex: 26.96, in: 26.62, ae: 22.78 },
    repair: { ex: 24.67, in: 61.93, ae: 43.27 },
    average: { ex: 35.2, in: 35.2, ae: 35.2 }
  },
  {
    model: "30B-A3B-Thinking",
    group: "Open-Source",
    generation: { ex: 47.37, in: 20.87, ae: 37.47 },
    editing: { ex: 19.82, in: 21.21, ae: 18.2 },
    repair: { ex: 18.08, in: 51.85, ae: 31.31 },
    average: { ex: 29.58, in: 29.58, ae: 29.58 }
  },
  {
    model: "30B-A3B-Instruct",
    group: "Open-Source",
    generation: { ex: 41.79, in: 20.8, ae: 29.28 },
    editing: { ex: 20.57, in: 20.97, ae: 17.93 },
    repair: { ex: 19.32, in: 50.71, ae: 31.35 },
    average: { ex: 28.08, in: 28.08, ae: 28.08 }
  }
];
