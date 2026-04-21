"use client";

import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { FindingItem } from "@/lib/types";

type FindingsSectionProps = {
  mainFindings: FindingItem[];
  additionalFindings: FindingItem[];
};

const difficultyData = [
  { level: "Easy", score: 72 },
  { level: "Medium", score: 54 },
  { level: "Hard", score: 31 }
];

export function FindingsSection({ mainFindings, additionalFindings }: FindingsSectionProps) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-3">
        {mainFindings.map((item, index) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.35, delay: index * 0.06 }}
          >
            <Card className="h-full">
              <CardHeader>
                <span className="text-xs font-semibold uppercase tracking-wide text-primary">{item.emphasis}</span>
                <CardTitle className="text-lg">{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{item.summary}</CardDescription>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Difficulty-Level Analysis</CardTitle>
            <CardDescription>
              Placeholder chart for final reported scores. Replace with paper figure once final numbers are frozen.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={difficultyData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" />
                <XAxis dataKey="level" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} domain={[0, 100]} />
                <Tooltip cursor={{ fill: "rgba(59,130,246,0.08)" }} />
                <Bar dataKey="score" fill="rgb(37, 99, 235)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <div className="grid gap-4">
          {additionalFindings.map((item) => (
            <Card key={item.title}>
              <CardHeader>
                <span className="text-xs font-semibold uppercase tracking-wide text-primary">{item.emphasis}</span>
                <CardTitle className="text-base">{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{item.summary}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}