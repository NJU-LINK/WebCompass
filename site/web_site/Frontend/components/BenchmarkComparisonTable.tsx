import type { ComparisonRow } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Check, X } from "lucide-react";

const columns: Array<{ key: keyof Omit<ComparisonRow, "benchmark" | "isWebCompass">; label: string }> = [
  { key: "size", label: "Size" },
  { key: "editingCount", label: "Edit (#)" },
  { key: "repairCount", label: "Repair (#)" },
  { key: "text", label: "Text" },
  { key: "image", label: "Image" },
  { key: "video", label: "Video" },
  { key: "generation", label: "Generation" },
  { key: "editing", label: "Editing" },
  { key: "repair", label: "Repair" },
  { key: "multiPage", label: "Multi-Page" },
  { key: "interaction", label: "Interaction" },
  { key: "visual", label: "Visual" },
  { key: "agentic", label: "Agentic Eval" },
  { key: "reverseDeterministicRepair", label: "Reverse Deterministic Repair" }
];

type BenchmarkComparisonTableProps = {
  rows: ComparisonRow[];
};

export function BenchmarkComparisonTable({ rows }: BenchmarkComparisonTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border/70">
      <table className="min-w-[1280px] w-full text-sm">
        <thead className="bg-muted/60">
          <tr>
            <th className="sticky left-0 bg-muted/60 px-4 py-3 text-left font-semibold">Benchmark</th>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3 text-center font-semibold">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.benchmark} className={cn("border-t border-border/60", row.isWebCompass && "bg-primary/5")}>
              <td
                className={cn(
                  "sticky left-0 px-4 py-3 font-medium",
                  row.isWebCompass ? "bg-primary/10 text-primary" : "bg-background"
                )}
              >
                {row.benchmark}
              </td>
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-3 text-center text-muted-foreground">
                  {renderCell(row, column.key)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderCell(row: ComparisonRow, key: keyof Omit<ComparisonRow, "benchmark" | "isWebCompass">) {
  if (key === "size") return row.size;
  if (key === "editingCount") return row.editingCount && row.editingCount > 0 ? row.editingCount : "-";
  if (key === "repairCount") return row.repairCount && row.repairCount > 0 ? row.repairCount : "-";
  if (!row[key]) {
    return (
      <span
        aria-label="Not supported"
        className="mx-auto inline-flex h-6 w-6 items-center justify-center rounded-full border border-rose-500/55 bg-rose-500/12 text-rose-700"
      >
        <X className="h-3.5 w-3.5" />
      </span>
    );
  }

  return (
    <span
      aria-label="Supported"
      className="mx-auto inline-flex h-6 w-6 items-center justify-center rounded-full border border-emerald-600/65 bg-emerald-600/20 text-emerald-800"
    >
      <Check className="h-3.5 w-3.5" />
    </span>
  );
}
