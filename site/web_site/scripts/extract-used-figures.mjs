import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const secDir = path.join(repoRoot, "Paper", "sec");
const outputPath = path.join(repoRoot, "Frontend", "data", "usedFigures.json");

const texFiles = fs
  .readdirSync(secDir)
  .filter((name) => name.endsWith(".tex"))
  .sort();

const includePattern = /\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}/g;
const refs = new Map();

for (const texFile of texFiles) {
  const abs = path.join(secDir, texFile);
  const content = fs.readFileSync(abs, "utf8");

  let match;
  while ((match = includePattern.exec(content)) !== null) {
    const raw = match[1].trim();
    const normalized = raw.replace(/\\/g, "/").replace(/^\.\//, "");

    if (!normalized.startsWith("figures/")) {
      continue;
    }

    const file = path.basename(normalized);
    refs.set(file, {
      file,
      path: normalized,
      referencedIn: texFile
    });
  }
}

const used = Array.from(refs.values()).sort((a, b) => a.file.localeCompare(b.file));

const payload = {
  generatedAt: new Date().toISOString(),
  from: "Paper/sec/*.tex",
  count: used.length,
  figures: used
};

fs.writeFileSync(outputPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
console.log(`Wrote ${used.length} entries to ${path.relative(repoRoot, outputPath)}`);
