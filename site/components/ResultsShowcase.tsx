"use client";

import { useMemo, useState } from "react";

import { FigureFallbackCard } from "@/components/figures/FigureFallbackCard";
import { FigureModal } from "@/components/figures/FigureModal";
import { InlineFigureCard } from "@/components/figures/InlineFigureCard";
import { pickFigureById } from "@/data/resultsShowcase";
import type { FigureItem } from "@/lib/types";
import { cn } from "@/lib/utils";

type ResultsShowcaseProps = {
  figures: FigureItem[];
  items: Array<{
    title: string;
    insight: string;
    figureId: string;
    order: number;
  }>;
};

export function ResultsShowcase({ figures, items }: ResultsShowcaseProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const activeFigure = useMemo(() => figures.find((f) => f.id === activeId) ?? null, [activeId, figures]);
  const orderedItems = useMemo(() => [...items].sort((a, b) => a.order - b.order), [items]);

  return (
    <>
      <div className="space-y-8">
        {orderedItems.map((item, index) => {
          const figure = pickFigureById(figures, item.figureId);
          if (!figure) return null;

          return (
            <div key={item.figureId} className={cn("rounded-2xl border border-border/70 bg-card/60 p-4 lg:p-5", index % 2 === 1 && "lg:px-6")}>
              {figure.hasRealAsset ? (
                <InlineFigureCard
                  figure={figure}
                  captionOverride={item.insight}
                  showTakeaway={false}
                  onOpen={() => setActiveId(figure.id)}
                />
              ) : (
                <FigureFallbackCard number={figure.number} title={figure.title} caption={item.insight || figure.caption} />
              )}
            </div>
          );
        })}
      </div>
      <FigureModal figure={activeFigure} open={Boolean(activeId)} onOpenChange={(open) => setActiveId(open ? activeId : null)} />
    </>
  );
}
