import type { FindingItem } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type InsightsSectionProps = {
  findings: FindingItem[];
};

export function InsightsSection({ findings }: InsightsSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {findings.map((item) => (
        <Card key={item.title} className="border-border/70">
          <CardHeader>
            <CardTitle className="text-base">{item.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{item.summary}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}