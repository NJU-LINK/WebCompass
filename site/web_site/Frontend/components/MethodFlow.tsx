import { ArrowRight } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const steps = [
  {
    title: "Data Construction",
    detail:
      "Human-in-the-loop collection, augmentation, and quality control across text/image/video sources."
  },
  {
    title: "Task Instantiation",
    detail:
      "Seven task categories spanning generation, editing, and repair with deterministic settings."
  },
  {
    title: "Task-aware Evaluation",
    detail:
      "Checklist-guided LLM-as-a-Judge for editing/repair and Agent-as-a-Judge for generation."
  }
];

export function MethodFlow() {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {steps.map((step, index) => (
        <Card key={step.title} className="relative border-border/70">
          <CardHeader>
            <CardTitle className="text-base">{step.title}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">{step.detail}</CardContent>
          {index < steps.length - 1 ? (
            <ArrowRight className="absolute right-3 top-3 hidden h-4 w-4 text-primary md:block" />
          ) : null}
        </Card>
      ))}
    </div>
  );
}