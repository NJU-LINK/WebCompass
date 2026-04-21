"use client";

import { ExternalLink } from "lucide-react";

import { withBasePath } from "@/lib/base-path";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import type { FigureItem } from "@/lib/types";

type FigureModalProps = {
  figure: FigureItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function FigureModal({ figure, open, onOpenChange }: FigureModalProps) {
  if (!figure) return null;

  const previewSrc = figure.previewSrc ? withBasePath(figure.previewSrc) : null;
  const fullSrc = figure.fullSrc ? withBasePath(figure.fullSrc) : null;
  const showPreview = previewSrc && figure.previewType !== "pdf";
  const pdfSrc = figure.fullType === "pdf" && fullSrc ? fullSrc : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl">
        <DialogHeader>
          <DialogTitle>
            {figure.number}: {figure.title}
          </DialogTitle>
          <DialogDescription>{figure.caption}</DialogDescription>
        </DialogHeader>

        {showPreview ? (
          <div className="overflow-hidden rounded-lg border border-border bg-white p-2">
            <img
              src={previewSrc}
              alt={figure.alt}
              className="mx-auto h-auto max-h-[80vh] w-full object-contain"
              loading="lazy"
            />
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-border bg-muted/20 p-6 text-sm text-muted-foreground">
            Preview asset pending.
          </div>
        )}

        {pdfSrc ? (
          <div className="flex justify-end">
            <Button asChild variant="outline" size="sm">
              <a href={pdfSrc} target="_blank" rel="noreferrer">
                Open Original PDF
                <ExternalLink className="ml-2 h-4 w-4" />
              </a>
            </Button>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
