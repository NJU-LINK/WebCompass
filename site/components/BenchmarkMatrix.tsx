import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type BenchmarkMatrixProps = {
  compact?: boolean;
};

const rows = ["Text", "Image", "Video"] as const;
const cols = ["Generation", "Editing", "Repair"] as const;

const cellMap: Record<string, { label: string; active: boolean }> = {
  "Text-Generation": { label: "Text-Guided Generation", active: true },
  "Text-Editing": { label: "Text-Guided Editing", active: true },
  "Text-Repair": { label: "Diagnostic Repair", active: true },
  "Image-Generation": { label: "Vision-Guided Generation", active: true },
  "Image-Editing": { label: "Vision-Guided Editing", active: true },
  "Image-Repair": { label: "Visual-Diagnostic Repair", active: true },
  "Video-Generation": { label: "Video-Guided Generation", active: true },
  "Video-Editing": { label: "Not Defined", active: false },
  "Video-Repair": { label: "Not Defined", active: false }
};

export function BenchmarkMatrix({ compact = false }: BenchmarkMatrixProps) {
  return (
    <Card className={cn("border-border/70", compact && "bg-background/70") }>
      <CardHeader className={cn(compact && "pb-3") }>
        <CardTitle className={cn("text-base", !compact && "text-lg")}>Multimodal Task Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2 text-xs md:text-sm">
          <div />
          {cols.map((col) => (
            <div key={col} className="rounded-md bg-muted px-2 py-2 text-center font-semibold text-foreground">
              {col}
            </div>
          ))}
          {rows.map((row) => (
            <div key={row} className="contents">
              <div key={`${row}-label`} className="rounded-md bg-muted px-2 py-2 text-center font-semibold text-foreground">
                {row}
              </div>
              {cols.map((col) => {
                const cell = cellMap[`${row}-${col}`];
                return (
                  <div
                    key={`${row}-${col}`}
                    className={cn(
                      "rounded-md border px-2 py-2 text-center leading-tight",
                      cell.active
                        ? "border-primary/40 bg-primary/10 text-primary"
                        : "border-border/60 bg-background text-muted-foreground"
                    )}
                  >
                    {compact ? cell.label.replace("-Guided ", "-") : cell.label}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
