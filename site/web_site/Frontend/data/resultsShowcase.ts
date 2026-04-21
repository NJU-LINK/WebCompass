import type { FigureItem } from "@/lib/types";

export const resultShowcase: Array<{
  title: string;
  insight: string;
  figureId: string;
}> = [
  {
    title: "Difficulty Scaling",
    insight: "Performance drops monotonically from Easy to Hard across generation, editing, and repair families.",
    figureId: "fig-diff-gen"
  },
  {
    title: "Interactivity Bottleneck",
    insight: "Interactivity remains the most fragile dimension under complex generation requirements.",
    figureId: "fig-consistency"
  },
  {
    title: "Editing Difficulty",
    insight: "Animation-heavy operations remain significantly harder than structure-preserving edits.",
    figureId: "fig-edit-subtask"
  },
  {
    title: "Repair Difficulty",
    insight: "Semantic defects demand stronger intent understanding than surface-level bug fixing.",
    figureId: "fig-repair-subtask"
  }
];

export function pickFigureById(figures: FigureItem[], id: string) {
  return figures.find((figure) => figure.id === id) ?? null;
}
