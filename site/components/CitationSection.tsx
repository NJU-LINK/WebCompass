"use client";

import { Check, Copy, ExternalLink } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

type CitationSectionProps = {
  bibtex: string;
  resources: { label: string; href: string }[];
};

export function CitationSection({ bibtex, resources }: CitationSectionProps) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(bibtex);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border/70 bg-muted/40 p-4 md:p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-foreground">BibTeX</h3>
          <Button onClick={onCopy} size="sm" variant="outline">
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>
        <pre className="overflow-x-auto rounded-lg bg-background p-4 text-xs leading-relaxed text-muted-foreground md:text-sm">
          <code>{bibtex}</code>
        </pre>
      </div>

      <div className="flex flex-wrap gap-3">
        {resources.map((resource) => (
          <Button key={resource.label} asChild variant="outline">
            <a href={resource.href} target="_blank" rel="noreferrer">
              {resource.label}
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>
        ))}
      </div>
    </div>
  );
}