import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PipelineStep } from "@/lib/types";

type EvaluationSectionProps = {
  steps: PipelineStep[];
};

export function EvaluationSection({ steps }: EvaluationSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {steps.map((step) => (
        <Card key={step.title}>
          <CardHeader>
            <CardTitle className="text-base">{step.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>{step.description}</CardDescription>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}