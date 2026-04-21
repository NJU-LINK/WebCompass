export type NavItem = {
  label: string;
  href: string;
};

export type LinkItem = {
  label: string;
  href: string;
};

export type HeroMetric = {
  label: string;
  value: number;
  suffix?: string;
};

export type HighlightItem = {
  title: string;
  description: string;
};

export type TaskCategory = {
  id: string;
  title: string;
  modality: "Text" | "Image" | "Video" | "Diagnostic";
  taskType: "Generation" | "Editing" | "Repair";
  description: string;
};

export type ComparisonRow = {
  benchmark: string;
  size: string;
  editingCount?: number;
  repairCount?: number;
  text: boolean;
  image: boolean;
  video: boolean;
  generation: boolean;
  editing: boolean;
  repair: boolean;
  multiPage: boolean;
  interaction: boolean;
  visual: boolean;
  agentic: boolean;
  reverseDeterministicRepair: boolean;
  isWebCompass?: boolean;
};

export type PipelineStep = {
  title: string;
  description: string;
  tags?: string[];
};

export type FindingItem = {
  title: string;
  summary: string;
  emphasis: string;
};

export type FigurePlacement = "overview" | "benchmark" | "method" | "results" | "gallery";
export type FigureSize = "hero" | "featured" | "standard" | "compact";
export type FigureAspectRatio = "auto" | "landscape" | "portrait" | "square";
export type FigureAssetType = "image" | "pdf";

export type FigureItem = {
  id: string;
  number: string;
  title: string;
  caption: string;
  takeaway?: string;
  sourceRef: string;
  previewSrc?: string;
  fullSrc?: string;
  previewType?: FigureAssetType;
  fullType?: FigureAssetType;
  alt: string;
  hasRealAsset: boolean;
  priority: "primary" | "secondary";
  placement: FigurePlacement;
  size: FigureSize;
  aspectRatio?: FigureAspectRatio;
  mediaFrameClass?: string;
  hideIfMissing?: boolean;
};

export type LimitationItem = {
  title: string;
  description: string;
};
