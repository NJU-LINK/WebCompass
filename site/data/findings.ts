import type { FindingItem } from "@/lib/types";

export const mainFindings: FindingItem[] = [
  {
    title: "Closed-source Models Lead by a Large Margin",
    summary:
      "Top closed-source systems score around 65.9 Avg Execution, while the best open-source model reaches 38.77, reflecting an approximately 25-point gap.",
    emphasis: "Main Results"
  },
  {
    title: "Interactivity is a Major Bottleneck in Generation",
    summary:
      "Difficulty increase causes steep degradation, especially on generation interactivity where complex user flows and state transitions are hard to preserve.",
    emphasis: "Generation"
  },
  {
    title: "Aesthetics Remains a Persistent Weakness",
    summary:
      "Across models, aesthetics is commonly the lowest or near-lowest dimension in generation/editing, even when execution appears strong.",
    emphasis: "Aesthetics"
  }
];

export const additionalFindings: FindingItem[] = [
  {
    title: "Animation-heavy Editing is Hardest",
    summary:
      "Parallax scrolling, page transitions, and particle effects are consistently harder than business-scenario operations.",
    emphasis: "Editing"
  },
  {
    title: "Semantic Defects are Hardest in Repair",
    summary:
      "Semantic Error is the lowest-scoring repair category, indicating difficulty in intent-level understanding beyond local patching.",
    emphasis: "Repair"
  },
  {
    title: "Consistency Matters More Than Isolated Wins",
    summary:
      "Harmonic-mean aggregation penalizes unstable low outliers, so robust cross-subtask consistency is more valuable than occasional peaks.",
    emphasis: "Consistency"
  }
];

export const findingsBlocks = [
  {
    id: "main-results",
    title: "Main Results",
    description:
      "Model rankings reveal complementary strengths, with no single model dominating generation, editing, and repair simultaneously."
  },
  {
    id: "task-breakdown",
    title: "Task-Type Breakdown",
    description:
      "Editing and repair expose distinct difficulty gradients and failure signatures at subtask level."
  },
  {
    id: "difficulty-analysis",
    title: "Difficulty-Level Analysis",
    description:
      "Scores decrease monotonically from Easy to Hard across dimensions and task families."
  },
  {
    id: "error-analysis",
    title: "Error Analysis / Insights",
    description:
      "Feature Missing, visual inconsistency, and unaddressed semantic defects dominate common failure modes."
  }
];