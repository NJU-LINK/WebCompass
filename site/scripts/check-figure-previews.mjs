import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const usedPath = path.join(root, "data", "usedFigures.json");
const publicFiguresDir = path.join(root, "public", "figures");

const used = JSON.parse(fs.readFileSync(usedPath, "utf8"));
const files = new Set(fs.readdirSync(publicFiguresDir));

const aliasMap = {
  "overview.pdf": "overview.png",
  "data_collection_pipeline.pdf": "data_collection_pipeline.png",
  "llm_as_judge.pdf": "Evaluation_Validity_verification.png",
  "agent_as_a_judge.pdf": "agent-as-a-judge.png",
  "benchmark_dim_comparison_gen.pdf": "Score_of_diff_difficulty.png",
  "edit_subtask_bars.pdf": "main_results_overview.png",
  "repair_subtask_bars.pdf": "check-list-score.png",
  "consistency_stability_linechart.pdf": "consistency_stability_linechart.png",
  "rank_comparison.pdf": "web-bench-arena-rank.png",
  "webcompass_radial.pdf": "webcompass_radial.png"
};

function candidates(pdf) {
  const base = pdf.replace(/\.pdf$/i, "");
  return [`${base}.png`, `${base}.webp`, `${base}.jpg`, `${base}.jpeg`, aliasMap[pdf]].filter(Boolean);
}

const report = used.figures
  .map((item) => item.file)
  .filter((file) => file.toLowerCase().endsWith(".pdf"))
  .map((pdf) => {
    const match = candidates(pdf).find((name) => files.has(name));
    return {
      source: pdf,
      preview: match ?? null,
      status: match ? "ok" : "missing"
    };
  });

const missing = report.filter((row) => row.status === "missing");

console.log(`PDF sources checked: ${report.length}`);
console.log(`Preview available: ${report.length - missing.length}`);
console.log(`Preview missing: ${missing.length}`);

if (missing.length > 0) {
  console.log("Missing preview assets:");
  for (const row of missing) console.log(`- ${row.source}`);
}

const outputPath = path.join(root, "data", "pdfPreviewAudit.json");
fs.writeFileSync(outputPath, `${JSON.stringify({ generatedAt: new Date().toISOString(), report }, null, 2)}\n`, "utf8");
console.log(`Wrote audit file: ${path.relative(root, outputPath)}`);
