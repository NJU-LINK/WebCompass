import { cn } from "@/lib/utils";
import type { MatrixCell, MatrixCol, MatrixRow, MultimodalMatrixData } from "@/data/multimodalMatrix";

type MultimodalMatrixProps = {
  data: MultimodalMatrixData;
  className?: string;
};

const colAccent: Record<MatrixCol, string> = {
  Generation: "from-sky-500/18 to-blue-500/18 border-sky-300/60 text-sky-800",
  Editing: "from-violet-500/16 to-indigo-500/16 border-violet-300/60 text-violet-800",
  Repair: "from-emerald-500/16 to-teal-500/16 border-emerald-300/60 text-emerald-800"
};

const rowAccent: Record<MatrixRow, string> = {
  Text: "bg-slate-100 text-slate-700",
  Image: "bg-slate-100 text-slate-700",
  Video: "bg-slate-100 text-slate-700"
};

function renderCell(cell: MatrixCell, col: MatrixCol) {
  if (!cell.label) {
    return (
      <div className="h-full min-h-[88px] rounded-xl border border-slate-200/70 bg-slate-50/90" aria-hidden="true" />
    );
  }

  return (
    <div
      className={cn(
        "group flex h-full min-h-[88px] items-center justify-center rounded-xl border bg-gradient-to-br px-3 py-3 text-center text-sm font-medium leading-snug shadow-sm transition duration-200",
        colAccent[col],
        cell.emphasis === "strong" && "ring-1 ring-current/20",
        "hover:-translate-y-0.5 hover:shadow-md hover:brightness-105"
      )}
    >
      {cell.label}
    </div>
  );
}

export function MultimodalMatrix({ data, className }: MultimodalMatrixProps) {
  const { rows, cols, cells } = data;

  return (
    <section
      aria-label="Multimodal Task Matrix"
      className={cn(
        "rounded-3xl border border-border/70 bg-white/80 p-4 shadow-sm backdrop-blur-sm md:p-6",
        className
      )}
    >
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-primary">Core Design</p>
          <h3 className="mt-1 text-xl font-semibold text-foreground md:text-2xl">Multimodal Task Matrix</h3>
          <p className="mt-1 text-sm text-muted-foreground">3 Modalities x 3 Task Types, covering 7 valid task categories.</p>
        </div>
      </div>

      <div className="hidden grid-cols-[130px_repeat(3,minmax(0,1fr))] gap-3 md:grid">
        <div />
        {cols.map((col) => (
          <div
            key={col}
            className={cn(
              "rounded-xl border px-3 py-3 text-center text-sm font-semibold",
              colAccent[col],
              "bg-gradient-to-br"
            )}
          >
            {col}
          </div>
        ))}

        {rows.map((row, rowIndex) => (
          <div key={row} className="contents">
            <div className={cn("rounded-xl px-3 py-3 text-center text-sm font-semibold", rowAccent[row])}>{row}</div>
            {cols.map((col, colIndex) => (
              <div key={`${row}-${col}`}>{renderCell(cells[rowIndex][colIndex], col)}</div>
            ))}
          </div>
        ))}
      </div>

      <div className="space-y-3 md:hidden">
        {rows.map((row, rowIndex) => (
          <div key={row} className="rounded-2xl border border-border/60 bg-slate-50/60 p-3">
            <div className={cn("mb-2 inline-flex rounded-md px-2 py-1 text-xs font-semibold", rowAccent[row])}>{row}</div>
            <div className="grid grid-cols-3 gap-2">
              {cols.map((col, colIndex) => (
                <div key={`${row}-${col}`} className="space-y-1">
                  <div className="text-center text-[11px] font-semibold text-muted-foreground">{col}</div>
                  {renderCell(cells[rowIndex][colIndex], col)}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
