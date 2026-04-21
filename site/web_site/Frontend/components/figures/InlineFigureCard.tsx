import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { withBasePath } from "@/lib/base-path";
import type { FigureItem } from "@/lib/types";
import { cn } from "@/lib/utils";

type InlineFigureCardProps = {
  figure: FigureItem;
  onOpen?: () => void;
  className?: string;
  showCaption?: boolean;
  captionOverride?: string;
  showTakeaway?: boolean;
};

const sizeMaxWidth: Record<FigureItem["size"], string> = {
  hero: "max-w-[1180px]",
  featured: "max-w-[1100px]",
  standard: "max-w-[980px]",
  compact: "max-w-[760px]"
};

const aspectRatioClass: Record<NonNullable<FigureItem["aspectRatio"]>, string> = {
  auto: "",
  landscape: "aspect-[16/10]",
  portrait: "aspect-[4/5]",
  square: "aspect-square"
};

const autoHeightClass: Record<FigureItem["size"], string> = {
  hero: "max-h-[760px]",
  featured: "max-h-[620px]",
  standard: "max-h-[520px]",
  compact: "max-h-[360px]"
};

export function InlineFigureCard({
  figure,
  onOpen,
  className,
  showCaption = true,
  captionOverride,
  showTakeaway = true
}: InlineFigureCardProps) {
  if (!figure.previewSrc || figure.previewType === "pdf") return null;
  const src = withBasePath(figure.previewSrc);
  const ratio = figure.aspectRatio ?? "auto";
  const description = captionOverride?.trim() ? captionOverride : figure.caption;

  return (
    <Card className={cn("overflow-hidden border-border/70 bg-card/95", className)}>
      <button type="button" onClick={onOpen} className="block w-full text-left">
        <div className="border-b border-border/60 bg-muted/10 p-2 md:p-3">
          <div className={cn("mx-auto overflow-hidden rounded-lg border border-border/60 bg-white", sizeMaxWidth[figure.size], figure.mediaFrameClass)}>
            {ratio === "auto" ? (
              <img
                src={src}
                alt={figure.alt}
                className={cn("mx-auto h-auto w-full object-contain", autoHeightClass[figure.size])}
                loading="lazy"
              />
            ) : (
              <div className={cn("relative w-full", aspectRatioClass[ratio])}>
                <img
                  src={src}
                  alt={figure.alt}
                  className="absolute inset-0 h-full w-full object-contain"
                  loading="lazy"
                />
              </div>
            )}
          </div>
        </div>
      </button>
      <CardHeader className="space-y-2 pb-1">
        <div className="text-xs font-medium text-primary">{figure.number}</div>
        <CardTitle className="text-base leading-snug md:text-lg">{figure.title}</CardTitle>
      </CardHeader>
      {showCaption ? (
        <CardContent className="pt-2">
          <CardDescription className="text-sm leading-relaxed">{description}</CardDescription>
          {showTakeaway && figure.takeaway ? <p className="mt-2 text-xs text-muted-foreground">Takeaway: {figure.takeaway}</p> : null}
        </CardContent>
      ) : null}
    </Card>
  );
}
