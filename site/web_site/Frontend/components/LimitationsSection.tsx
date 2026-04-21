import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LimitationItem } from "@/lib/types";

type LimitationsSectionProps = {
  items: LimitationItem[];
};

export function LimitationsSection({ items }: LimitationsSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <Card key={item.title}>
          <CardHeader>
            <CardTitle className="text-base">{item.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-muted-foreground">{item.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}