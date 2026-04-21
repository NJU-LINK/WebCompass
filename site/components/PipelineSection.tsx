import { ArrowRight } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PipelineStep } from "@/lib/types";

type PipelineSectionProps = {
  steps: PipelineStep[];
};

export function PipelineSection({ steps }: PipelineSectionProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {steps.map((step, index) => (
        <Card key={step.title} className="relative overflow-hidden">
          <CardHeader>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary">Step {index + 1}</div>
            <CardTitle className="text-lg">{step.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <CardDescription>{step.description}</CardDescription>
            {step.tags ? (
              <div className="flex flex-wrap gap-2">
                {step.tags.map((tag) => (
                  <span key={tag} className="rounded-full border border-border/70 bg-muted px-2 py-1 text-xs text-muted-foreground">
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
            {index < steps.length - 1 ? <ArrowRight className="absolute right-4 top-4 h-4 w-4 text-muted-foreground" /> : null}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}