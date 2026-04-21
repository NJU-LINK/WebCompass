import type { MainResultsRow } from "@/data/mainResultsTable";
import { cn } from "@/lib/utils";

type MainResultsTableProps = {
  rows: MainResultsRow[];
};

type ScoreTriplet = { ex: number; in: number; ae: number };

function collectScores(rows: MainResultsRow[]) {
  const values: number[] = [];
  for (const row of rows) {
    const groups: ScoreTriplet[] = [row.generation, row.editing, row.repair];
    for (const g of groups) values.push(g.ex, g.in, g.ae);
    values.push(row.average.ex);
  }
  return values;
}

function scoreStyle(value: number, min: number, max: number) {
  const ratio = max === min ? 0 : (value - min) / (max - min);
  const alpha = 0.08 + ratio * 0.26;
  const text = ratio > 0.72 ? "rgb(22 101 52)" : ratio > 0.5 ? "rgb(21 94 117)" : "rgb(51 65 85)";
  return {
    backgroundColor: `rgba(16, 185, 129, ${alpha.toFixed(3)})`,
    color: text
  };
}

function SectionHeader({ label, tone }: { label: string; tone: string }) {
  return (
    <tr>
      <td colSpan={11} className={cn("px-3 py-2 text-xs font-semibold uppercase tracking-wide", tone)}>
        {label}
      </td>
    </tr>
  );
}

function MetricCell({ value, min, max }: { value: number; min: number; max: number }) {
  return (
    <td className="px-1.5 py-2 text-center text-[11px] font-medium md:text-xs" style={scoreStyle(value, min, max)}>
      {value.toFixed(2)}
    </td>
  );
}

function DesktopRow({ row, min, max }: { row: MainResultsRow; min: number; max: number }) {
  return (
    <tr className="border-t border-border/60">
      <td className="px-3 py-2 text-left text-[11px] font-semibold text-slate-700 md:text-xs lg:text-sm">
        <span className="line-clamp-2">{row.model}</span>
      </td>
      <MetricCell value={row.generation.ex} min={min} max={max} />
      <MetricCell value={row.generation.in} min={min} max={max} />
      <MetricCell value={row.generation.ae} min={min} max={max} />
      <MetricCell value={row.editing.ex} min={min} max={max} />
      <MetricCell value={row.editing.in} min={min} max={max} />
      <MetricCell value={row.editing.ae} min={min} max={max} />
      <MetricCell value={row.repair.ex} min={min} max={max} />
      <MetricCell value={row.repair.in} min={min} max={max} />
      <MetricCell value={row.repair.ae} min={min} max={max} />
      <MetricCell value={row.average.ex} min={min} max={max} />
    </tr>
  );
}

function MobileMetricBlock({
  title,
  values,
  min,
  max,
  labels
}: {
  title: string;
  values: ScoreTriplet;
  min: number;
  max: number;
  labels: [string, string, string];
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-white/90 p-2">
      <div className="mb-1 text-[11px] font-semibold text-slate-600">{title}</div>
      <div className="grid grid-cols-3 gap-1 text-[11px]">
        <div className="text-center text-muted-foreground">{labels[0]}</div>
        <div className="text-center text-muted-foreground">{labels[1]}</div>
        <div className="text-center text-muted-foreground">{labels[2]}</div>
        <div className="rounded px-1 py-1 text-center" style={scoreStyle(values.ex, min, max)}>{values.ex.toFixed(2)}</div>
        <div className="rounded px-1 py-1 text-center" style={scoreStyle(values.in, min, max)}>{values.in.toFixed(2)}</div>
        <div className="rounded px-1 py-1 text-center" style={scoreStyle(values.ae, min, max)}>{values.ae.toFixed(2)}</div>
      </div>
    </div>
  );
}

function MobileRow({ row, min, max }: { row: MainResultsRow; min: number; max: number }) {
  return (
    <article className="rounded-xl border border-border/70 bg-white/95 p-3">
      <h4 className="text-sm font-semibold text-slate-800">{row.model}</h4>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <MobileMetricBlock title="Generation" values={row.generation} labels={["RUN", "SPI", "DSQ"]} min={min} max={max} />
        <MobileMetricBlock title="Editing" values={row.editing} labels={["ITG", "FTI", "STC"]} min={min} max={max} />
        <MobileMetricBlock title="Repair" values={row.repair} labels={["RCT", "ITI", "RFF"]} min={min} max={max} />
        <div className="rounded-lg border border-border/60 bg-white/90 p-2">
          <div className="mb-1 text-[11px] font-semibold text-slate-600">Overall</div>
          <div className="rounded px-1 py-2 text-center text-xs font-medium" style={scoreStyle(row.average.ex, min, max)}>
            {row.average.ex.toFixed(2)}
          </div>
        </div>
      </div>
    </article>
  );
}

export function MainResultsTable({ rows }: MainResultsTableProps) {
  const values = collectScores(rows);
  const min = Math.min(...values);
  const max = Math.max(...values);

  const closed = rows.filter((row) => row.group === "Closed-Source");
  const open = rows.filter((row) => row.group === "Open-Source");

  return (
    <div className="space-y-4">
      <div className="hidden rounded-2xl border border-border/70 bg-white/95 p-3 shadow-sm lg:block">
        <table className="w-full table-fixed border-separate border-spacing-0 text-xs">
          <colgroup>
            <col style={{ width: "22%" }} />
            {Array.from({ length: 10 }).map((_, i) => (
              <col key={i} style={{ width: "7.8%" }} />
            ))}
          </colgroup>
          <thead>
            <tr className="bg-slate-100/90 text-slate-700">
              <th rowSpan={2} className="rounded-l-lg px-3 py-2 text-left text-xs font-semibold">Model</th>
              <th colSpan={3} className="px-2 py-2 text-center text-xs font-semibold">Generation</th>
              <th colSpan={3} className="px-2 py-2 text-center text-xs font-semibold">Editing</th>
              <th colSpan={3} className="px-2 py-2 text-center text-xs font-semibold">Repair</th>
              <th rowSpan={2} className="rounded-r-lg px-2 py-2 text-center text-xs font-semibold">Overall</th>
            </tr>
            <tr className="bg-slate-50/90 text-slate-600">
              {["RUN", "SPI", "DSQ", "ITG", "FTI", "STC", "RCT", "ITI", "RFF"].map((m) => (
                <th key={m} className="px-1 py-1 text-center text-[11px] font-medium">{m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <SectionHeader label="Closed-Source Large Language Models" tone="bg-sky-50 text-sky-900" />
            {closed.map((row) => (
              <DesktopRow key={row.model} row={row} min={min} max={max} />
            ))}
            <SectionHeader label="Qwen3-VL Series Open-Source Large Language Models" tone="bg-emerald-50 text-emerald-900" />
            {open.map((row) => (
              <DesktopRow key={row.model} row={row} min={min} max={max} />
            ))}
          </tbody>
        </table>
      </div>

      <div className="space-y-3 lg:hidden">
        <div className="text-xs font-semibold uppercase tracking-wide text-sky-800">Closed-Source Large Language Models</div>
        {closed.map((row) => (
          <MobileRow key={row.model} row={row} min={min} max={max} />
        ))}

        <div className="pt-2 text-xs font-semibold uppercase tracking-wide text-emerald-800">Qwen3-VL Series Open-Source Large Language Models</div>
        {open.map((row) => (
          <MobileRow key={row.model} row={row} min={min} max={max} />
        ))}
      </div>
    </div>
  );
}
