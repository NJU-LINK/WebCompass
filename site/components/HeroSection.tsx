import { ArrowUpRight, BadgeCheck } from "lucide-react";

import { MultimodalMatrix } from "@/components/MultimodalMatrix";
import { StatsStrip } from "@/components/StatsStrip";
import { Button } from "@/components/ui/button";
import { multimodalMatrix } from "@/data/multimodalMatrix";
import type { HeroMetric, LinkItem } from "@/lib/types";

type HeroSectionProps = {
  title: string;
  subtitle: string;
  tagline: string;
  authors: string;
  affiliations: string;
  contacts?: string;
  links: LinkItem[];
  arxivBadge: string;
  metrics: HeroMetric[];
};

export function HeroSection({
  title,
  subtitle,
  tagline,
  authors,
  affiliations,
  contacts,
  links,
  arxivBadge,
  metrics
}: HeroSectionProps) {
  return (
    <section id="top" className="relative overflow-hidden pt-28">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-[-240px] h-[560px] w-[760px] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(56,189,248,0.22),rgba(59,130,246,0.08),transparent_72%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(255,255,255,0),rgba(255,255,255,1)_78%)]" />
      </div>

      <div className="container pb-16">
        <div className="mx-auto max-w-4xl text-center">
          <p className="text-sm font-medium tracking-wide text-primary">Official Project Page</p>
          <h1 className="mt-4 text-balance text-4xl font-semibold tracking-tight text-foreground md:text-6xl">{title}</h1>
          <p className="mt-4 text-balance text-lg text-muted-foreground md:text-2xl">{subtitle}</p>
          <p className="mt-4 text-pretty text-base font-medium text-foreground md:text-lg">
            Benchmarking Web Coding Agents Across Multimodal Inputs and Full Development Lifecycle
          </p>
          <p className="mt-4 text-pretty leading-relaxed text-muted-foreground">{tagline}</p>
          <div className="mt-6 space-y-1 text-sm text-muted-foreground">
            <p>{authors}</p>
            <p>{affiliations}</p>
            {contacts ? <p>Contact: {contacts}</p> : null}
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            {links.map((link, index) => (
              <Button key={link.label} asChild variant={index === 0 ? "default" : "outline"}>
                <a href={link.href} target={link.href.startsWith("#") ? "_self" : "_blank"} rel="noreferrer">
                  {link.label}
                  <ArrowUpRight className="h-4 w-4" />
                </a>
              </Button>
            ))}
            <Button asChild variant="secondary">
              <a href={arxivBadge} target="_blank" rel="noreferrer">
                <BadgeCheck className="h-4 w-4" />
                arXiv Badge (Placeholder)
              </a>
            </Button>
          </div>
        </div>

        <div className="mx-auto mt-10 w-full max-w-7xl">
          <MultimodalMatrix data={multimodalMatrix} />
        </div>

        <div className="mx-auto mt-10 max-w-6xl">
          <StatsStrip metrics={metrics} />
        </div>
      </div>
    </section>
  );
}
