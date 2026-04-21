import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDir, "..");

function findPaperSecDir(startDir) {
  let current = startDir;

  while (true) {
    const candidate = path.join(current, "Paper", "sec");
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate;
    }

    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }

  throw new Error(`Unable to locate Paper/sec from ${startDir}`);
}

const secDir = findPaperSecDir(frontendRoot);
const outputPath = path.join(frontendRoot, "data", "usedFigures.json");

const texFiles = fs
  .readdirSync(secDir)
  .filter((name) => name.endsWith(".tex"))
  .sort();

const includePattern = /\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}/g;
const refs = new Map();

function stripTexComments(content) {
  return content
    .split(/\r?\n/)
    .map((line) => {
      let out = "";
      for (let i = 0; i < line.length; i += 1) {
        const ch = line[i];
        if (ch === "%" && (i === 0 || line[i - 1] !== "\\")) {
          break;
        }
        out += ch;
      }
      return out;
    })
    .join("\n");
}

for (const texFile of texFiles) {
  const abs = path.join(secDir, texFile);
  const content = stripTexComments(fs.readFileSync(abs, "utf8"));

  let match;
  while ((match = includePattern.exec(content)) !== null) {
    const raw = match[1].trim();
    const normalized = raw.replace(/\\/g, "/").replace(/^\.\//, "");
    if (!normalized.startsWith("figures/")) continue;

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
console.log(`Wrote ${used.length} entries to ${path.relative(frontendRoot, outputPath)}`);
