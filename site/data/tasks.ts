import type { PipelineStep, TaskCategory } from "@/lib/types";

export const taskCategories: TaskCategory[] = [
  {
    id: "tg-gen",
    title: "Text-Guided Generation",
    modality: "Text",
    taskType: "Generation",
    description:
      "Input: textual specification covering content, interactions, and visual appearance. Output: a complete runnable web repository."
  },
  {
    id: "vg-gen",
    title: "Vision-Guided Generation",
    modality: "Image",
    taskType: "Generation",
    description:
      "Input: screenshots (main/subpages and dynamic keyframes). Output: a repository matching visual style and interaction behavior."
  },
  {
    id: "vidg-gen",
    title: "Video-Guided Generation",
    modality: "Video",
    taskType: "Generation",
    description:
      "Input: interaction recording video. Output: a repository consistent with demonstrated dynamic behavior and appearance."
  },
  {
    id: "tg-edit",
    title: "Text-Guided Editing",
    modality: "Text",
    taskType: "Editing",
    description:
      "Input: source repository + text instruction. Output: code patch that satisfies requirement updates without leaking implementation hints."
  },
  {
    id: "vg-edit",
    title: "Vision-Guided Editing",
    modality: "Image",
    taskType: "Editing",
    description:
      "Input: source repository + screenshot + instruction. Output: code patch aligned with visual target and requested edits."
  },
  {
    id: "diag-repair",
    title: "Diagnostic Repair",
    modality: "Diagnostic",
    taskType: "Repair",
    description:
      "Input: source repository + issue description. Output: repair patch that resolves defects under deterministic inverse verification."
  },
  {
    id: "vdiag-repair",
    title: "Visual-Diagnostic Repair",
    modality: "Image",
    taskType: "Repair",
    description:
      "Input: source repository + screenshot + issue description. Output: patch that repairs both visible and underlying diagnostic issues."
  }
];

export const whyWebCompass = [
  {
    title: "Unified Lifecycle Coverage",
    description: "WebCompass jointly evaluates generation, editing, and repair instead of isolating a single stage."
  },
  {
    title: "Multimodal Inputs",
    description: "Tasks are grounded in text, image, and video inputs, matching real request channels in web engineering."
  },
  {
    title: "Behavior-aware Evaluation",
    description: "Evaluation explicitly scores Execution, Interactivity, and Aesthetics with evidence-grounded judging protocols."
  }
];

export const constructionPipeline: PipelineStep[] = [
  {
    title: "Text-Guided Generation Collection and Query Refinement",
    description:
      "Collect queries from WebGen-Bench, ArtifactsBench, BigCode Arena, and V0, then refine underspecified requests into structured design documents.",
    tags: ["Dedup + Clustering", "Difficulty Labeling", "123 Queries"]
  },
  {
    title: "Vision-Guided Generation Augmentation",
    description:
      "Augment screenshots with subpage captures, keyframes, and multi-page relation markers to better represent dynamic and project-level scenarios.",
    tags: ["Screenshot Augmentation", "Keyframes", "Multi-page"]
  },
  {
    title: "Video-Guided Generation Recording",
    description:
      "Record interaction-rich browsing trajectories from selected V0/Figma webpages to preserve temporal behavior evidence.",
    tags: ["Interaction Trajectories", "Temporal Signals"]
  },
  {
    title: "Shared Prototype Pool for Editing and Repair",
    description:
      "Build prototypes with length filtering, automatic quality scoring, human curation, and single-/multi-page expansion.",
    tags: ["32k-64k Length Band", "GPT-4o Quality Filter", "50 Prototypes"]
  },
  {
    title: "Deterministic Reverse Repair Construction",
    description:
      "Inject 11 defect categories and attach exact inverse search/replace annotations to guarantee deterministic, verifiable repair targets.",
    tags: ["Defect Injection", "Reverse Search/Replace", "11 Defect Types"]
  },
  {
    title: "Three-layer Quality Control",
    description:
      "Run automated validation, LLM-assisted screening, and final expert review for executability, instruction quality, and annotation consistency.",
    tags: ["Automated Checks", "LLM Screening", "Human Curation"]
  }
];

export const evaluationPipeline: PipelineStep[] = [
  {
    title: "LLM-as-a-Judge for Editing and Repair",
    description:
      "Judge receives requirements, source repository, predicted patch, runtime logs, and before/after screenshots, then scores checklist items in structured JSON."
  },
  {
    title: "Agent-as-a-Judge for Generation",
    description:
      "Agent evaluates in real browser via checklist generation, interaction execution, adaptive verification, and evidence-grounded scoring."
  },
  {
    title: "Execution / Interactivity / Aesthetics",
    description:
      "Both paradigms use the same three dimensions, with safeguards including checklist immutability, selector-only adaptation, and mandatory evidence grounding."
  }
];

export const benchmarkFacts = {
  scale: "1526 tasks",
  taskCounts: {
    textGuidedGeneration: 123,
    visionGuidedGeneration: 109,
    videoGuidedGeneration: 94,
    textGuidedEditing: 300,
    visionGuidedEditing: 300,
    diagnosticRepair: 300,
    visualDiagnosticRepair: 300
  },
  difficulty: ["Easy", "Medium", "Hard"],
  generationDomains: 15,
  editingOperationTypes: 16,
  repairDefectCategories: 11
};