import { Check } from "lucide-react";

import { SectionContainer } from "@/components/SectionContainer";
import { SectionHeading } from "@/components/SectionHeading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type AbstractSectionProps = {
  abstract: string;
  highlights: string[];
  sourceNote?: string;
};

export function AbstractSection({ abstract, highlights, sourceNote }: AbstractSectionProps) {
  return (
    <SectionContainer id="overview">
      <SectionHeading
        eyebrow="Abstract / Overview"
        title="Why WebCompass"
        description={abstract}
      />
      {sourceNote ? <p className="mx-auto mb-6 max-w-4xl text-xs text-muted-foreground">{sourceNote}</p> : null}
      <Card className="mx-auto max-w-4xl">
        <CardHeader>
          <CardTitle className="text-xl">Core Contributions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {highlights.map((item) => (
              <div key={item} className="flex items-start gap-3 rounded-lg border border-border/60 bg-background/70 p-3">
                <Check className="mt-0.5 h-4 w-4 text-primary" />
                <p className="text-sm text-muted-foreground">{item}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </SectionContainer>
  );
}
