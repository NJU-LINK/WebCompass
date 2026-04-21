import type { FigureItem } from "@/lib/types";

export const resultShowcase: Array<{
  title: string;
  insight: string;
  figureId: string;
  order: number;
}> = [
  {
    title: "Ranking Agreement with Human Evaluation",
    insight: "Automatic agent-based ranking is closely aligned with human ranking across major model families.",
    figureId: "fig-rank",
    order: 7
  },
  {
    title: "Editing Difficulty",
    insight:
      "Animation-heavy operations remain significantly harder than structure-preserving edits. The gap is most visible in tasks requiring coordinated motion timing, transition continuity, and multi-element synchronization, where otherwise strong models still show unstable behavior.",
    figureId: "fig-edit-subtask",
    order: 8
  },
  {
    title: "Repair Difficulty",
    insight:
      "Semantic defects demand stronger intent understanding than surface-level bug fixing. Compared with syntactic and style-level repairs, semantic corrections require models to infer page-level goals and preserve interaction logic across components, which remains a persistent failure mode.",
    figureId: "fig-repair-subtask",
    order: 9
  },
  {
    title: "Consistency Under Repeated Sampling",
    insight:
      "Worst-of-N analysis shows that consistency is a stronger reliability signal than isolated wins. Even when a model can occasionally produce high-scoring outputs, robustness drops when evaluated over repeated runs, indicating that stable performance under heterogeneous constraints is still challenging.",
    figureId: "fig-consistency",
    order: 10
  }
];

export function pickFigureById(figures: FigureItem[], id: string) {
  return figures.find((figure) => figure.id === id) ?? null;
}
