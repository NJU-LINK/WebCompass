import type { LinkItem, NavItem } from "@/lib/types";

export const siteConfig = {
  name: "WebCompass",
  title: "WebCompass",
  subtitle: "Towards Holistic Evaluation of Web Coding for Multimodal Code Models",
  tagline:
    "WebCompass unifies text-, image-, and video-grounded web coding tasks across generation, editing, and repair, with task-aware evaluation for execution, interactivity, and aesthetics.",
  description:
    "Official project page for WebCompass: Towards Holistic Evaluation of Web Coding for Multimodal Code Models.",
  authors:
    "Xinping Lei(†), Xinyu Che(†), Junqi Xiong(†), Chenchen Zhang(†), Yukai Huang(†), Chenyu Zhou(†), Haoyang Huang, Minghao Liu, Letian Zhu, Hongyi Ye, Jinhua Hao, Ken Deng, Zizheng Zhan, Han Li, Dailin Li, Yifan Yao, Ming Sun, Zhaoxiang Zhang, Jiaheng Liu(*)",
  affiliations:
    "Nanjing University · Kuaishou Technology · (†) Equal contribution · (*) Corresponding author",
  contacts: "liujiaheng@nju.edu.cn; l1874493887@gmail.com",
  builtWith: "Next.js, Tailwind CSS, Framer Motion, shadcn/ui",
  links: {
    paper: "https://arxiv.org/abs/2604.18224",
    github: "https://github.com/NJU-LINK/WebCompass",
    huggingface: "https://huggingface.co/papers/2604.18224",
    dataset: "https://huggingface.co/datasets/NJU-LINK/WebCompass",
    arxivBadge: "https://arxiv.org/abs/2604.18224"
  }
};

export const navItems: NavItem[] = [
  { label: "Overview", href: "#overview" },
  { label: "Design", href: "#design" },
  { label: "Method", href: "#method" },
  { label: "Results", href: "#results" },
  { label: "Figures", href: "#figures" },
  { label: "Insights", href: "#insights" },
  { label: "Limitations", href: "#limitations" },
  { label: "Citation", href: "#citation" }
];

export const heroLinks: LinkItem[] = [
  { label: "Paper", href: siteConfig.links.paper },
  { label: "GitHub", href: siteConfig.links.github },
  { label: "Hugging Face", href: siteConfig.links.huggingface },
  { label: "Citation", href: "#citation" }
];

export const overviewHighlights = [
  "Unified lifecycle coverage across generation, editing, and repair with text/image/video inputs.",
  "Rigorous and deterministic task construction with reverse verifiable repair annotations.",
  "Task-aware evaluation: Agent-as-a-Judge for generation, checklist-guided LLM-as-a-Judge for editing/repair.",
  "Three shared evaluation dimensions: Execution, Interactivity, and Aesthetics.",
  "Realistic web engineering scenarios emphasizing multi-page behavior and interaction fidelity."
];

export const overviewAbstract =
  "Evaluating web coding requires more than code correctness: success depends on runtime execution, interaction behavior, and visual quality in browser environments. WebCompass addresses this gap with a unified multimodal benchmark spanning text, image, and video inputs, and lifecycle tasks across generation, editing, and repair. The benchmark is designed for realistic front-end engineering scenarios with deterministic construction and evidence-grounded evaluation.";

