import { Card, CardContent } from "@/components/ui/card";

type FigureFallbackCardProps = {
  number: string;
  title: string;
  caption: string;
};

export function FigureFallbackCard({ number, title, caption }: FigureFallbackCardProps) {
  return (
    <Card className="border-dashed border-border/70 bg-muted/20">
      <CardContent className="p-4">
        <p className="text-xs font-medium text-primary">{number}</p>
        <h4 className="mt-1 text-sm font-semibold text-foreground">{title}</h4>
        <p className="mt-2 text-xs text-muted-foreground">Figure asset pending.</p>
        <p className="mt-1 text-xs text-muted-foreground">{caption}</p>
      </CardContent>
    </Card>
  );
}
