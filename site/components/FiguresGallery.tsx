"use client";

import { useMemo, useState } from "react";

import { FigureModal } from "@/components/figures/FigureModal";
import { GalleryFigureCard } from "@/components/figures/GalleryFigureCard";
import type { FigureItem } from "@/lib/types";

type FiguresGalleryProps = {
  figures: FigureItem[];
};

export function FiguresGallery({ figures }: FiguresGalleryProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const selected = useMemo(() => figures.find((item) => item.id === activeId) ?? null, [activeId, figures]);

  return (
    <>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {figures.map((figure) => (
          <GalleryFigureCard key={figure.id} figure={figure} onOpen={() => setActiveId(figure.id)} />
        ))}
      </div>
      <FigureModal figure={selected} open={Boolean(activeId)} onOpenChange={(open) => setActiveId(open ? activeId : null)} />
    </>
  );
}
