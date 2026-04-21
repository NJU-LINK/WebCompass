import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { TaskCategory } from "@/lib/types";

type OverviewMatrixProps = {
  tasks: TaskCategory[];
  whyItems: { title: string; description: string }[];
};

export function OverviewMatrix({ tasks, whyItems }: OverviewMatrixProps) {
  return (
    <div className="space-y-10">
      <div className="rounded-2xl border border-border/70 bg-card/70 p-5 md:p-8">
        <div className="mb-5 flex flex-wrap items-center gap-2">
          <Badge>3 Modalities</Badge>
          <Badge>3 Task Types</Badge>
          <Badge>7 Task Categories</Badge>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {tasks.map((task) => (
            <Card key={task.id} className="h-full border-border/60">
              <CardHeader className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Badge className="bg-primary/10 text-primary">{task.modality}</Badge>
                  <Badge>{task.taskType}</Badge>
                </div>
                <CardTitle className="text-lg">{task.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{task.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {whyItems.map((item) => (
          <Card key={item.title}>
            <CardHeader>
              <CardTitle className="text-base">{item.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{item.description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}