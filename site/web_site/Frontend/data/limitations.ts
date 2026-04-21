import type { LimitationItem } from "@/lib/types";

export const limitations: LimitationItem[] = [
  {
    title: "Front-end Focus",
    description:
      "WebCompass currently targets front-end development (HTML/CSS/JavaScript and front-end frameworks) and does not yet cover back-end or deployment workflows."
  },
  {
    title: "Structured Queries vs. Creative Intent",
    description:
      "Structured design documents improve determinism and reproducibility, but they emphasize instruction-following more than open-ended creative divergence."
  },
  {
    title: "Limited Real-time Evaluation for Highly Dynamic Pages",
    description:
      "Time-sensitive behaviors in rapidly changing pages (e.g., games and highly dynamic state transitions) remain challenging for current automated protocols."
  },
  {
    title: "Static Benchmark and Contamination Risk",
    description:
      "As a static benchmark, long-term contamination risk remains possible and may require periodic benchmark refresh or dynamic task generation."
  },
  {
    title: "Evaluation Cost",
    description:
      "Agent-as-a-Judge involves browser execution, interaction loops, and iterative test synthesis, making evaluation more computationally expensive."
  }
];