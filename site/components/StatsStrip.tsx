"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import type { HeroMetric } from "@/lib/types";

function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    let raf = 0;
    const start = performance.now();

    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      setValue(Math.floor(progress * target));
      if (progress < 1) raf = requestAnimationFrame(step);
    };

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);

  return value;
}

type StatsStripProps = {
  metrics: HeroMetric[];
};

export function StatsStrip({ metrics }: StatsStripProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric, index) => (
        <StatCard key={metric.label} metric={metric} index={index} />
      ))}
    </div>
  );
}

function StatCard({ metric, index }: { metric: HeroMetric; index: number }) {
  const value = useCountUp(metric.value);
  const display = useMemo(() => `${value.toLocaleString()}${metric.suffix ?? ""}`, [value, metric.suffix]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: index * 0.05 }}
      className="rounded-xl border border-border/70 bg-card/75 p-5 shadow-sm backdrop-blur"
    >
      <p className="text-2xl font-semibold text-foreground md:text-3xl">{display}</p>
      <p className="mt-1 text-sm text-muted-foreground">{metric.label}</p>
    </motion.div>
  );
}