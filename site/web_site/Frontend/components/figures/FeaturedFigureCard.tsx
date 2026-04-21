import type { FigureItem } from "@/lib/types";

import { InlineFigureCard } from "@/components/figures/InlineFigureCard";

type FeaturedFigureCardProps = {
  figure: FigureItem;
  onOpen?: () => void;
};

export function FeaturedFigureCard({ figure, onOpen }: FeaturedFigureCardProps) {
  return <InlineFigureCard figure={figure} onOpen={onOpen} className="shadow-sm" />;
}
