export type MatrixRow = "Text" | "Image" | "Video";
export type MatrixCol = "Generation" | "Editing" | "Repair";

export type MatrixCell = {
  label: string | null;
  emphasis?: "normal" | "strong";
};

export type MultimodalMatrixData = {
  rows: MatrixRow[];
  cols: MatrixCol[];
  cells: MatrixCell[][];
};

export const multimodalMatrix: MultimodalMatrixData = {
  rows: ["Text", "Image", "Video"],
  cols: ["Generation", "Editing", "Repair"],
  cells: [
    [
      { label: "Text-Guided Generation", emphasis: "strong" },
      { label: "Text-Guided Editing", emphasis: "normal" },
      { label: "Diagnostic Repair", emphasis: "normal" }
    ],
    [
      { label: "Vision-Guided Generation", emphasis: "normal" },
      { label: "Vision-Guided Editing", emphasis: "normal" },
      { label: "Visual-Diagnostic Repair", emphasis: "strong" }
    ],
    [
      { label: "Video-Guided Generation", emphasis: "strong" },
      { label: null },
      { label: null }
    ]
  ]
};
