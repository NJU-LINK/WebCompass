"use client";

import { useState } from "react";

import { FeaturedFigureCard } from "@/components/figures/FeaturedFigureCard";
import { FigureFallbackCard } from "@/components/figures/FigureFallbackCard";
import { FigureModal } from "@/components/figures/FigureModal";
import type { FigureItem } from "@/lib/types";

type InlineFigureSpotlightProps = {
  figure: FigureItem;
};

export function InlineFigureSpotlight({ figure }: InlineFigureSpotlightProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {figure.hasRealAsset ? (
        <FeaturedFigureCard figure={figure} onOpen={() => setOpen(true)} />
      ) : (
        <FigureFallbackCard number={figure.number} title={figure.title} caption={figure.caption} />
      )}
      <FigureModal figure={figure} open={open} onOpenChange={setOpen} />
    </>
  );
}
