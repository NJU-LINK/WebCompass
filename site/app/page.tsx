"use client";

import { AbstractSection } from "@/components/AbstractSection";
import { BackToTop } from "@/components/BackToTop";
import { BenchmarkComparisonTable } from "@/components/BenchmarkComparisonTable";
import { CitationSection } from "@/components/CitationSection";
import { ConclusionSection } from "@/components/ConclusionSection";
import { EvaluationSection } from "@/components/EvaluationSection";
import { FiguresGallery } from "@/components/FiguresGallery";
import { Footer } from "@/components/Footer";
import { InlineFigureCard } from "@/components/figures/InlineFigureCard";
import { InlineFigureSpotlight } from "@/components/figures/InlineFigureSpotlight";
import { HeroSection } from "@/components/HeroSection";
import { InsightsSection } from "@/components/InsightsSection";
import { LimitationsSection } from "@/components/LimitationsSection";
import { MainResultsTable } from "@/components/MainResultsTable";
import { MethodFlow } from "@/components/MethodFlow";
import { Navbar } from "@/components/Navbar";
import { OverviewMatrix } from "@/components/OverviewMatrix";
import { PaperSourceNote } from "@/components/PaperSourceNote";
import { PipelineSection } from "@/components/PipelineSection";
import { ResultsShowcase } from "@/components/ResultsShowcase";
import { SectionContainer } from "@/components/SectionContainer";
import { SectionHeading } from "@/components/SectionHeading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { citation } from "@/data/citation";
import { comparisonRows } from "@/data/comparison";
import { getFiguresByPlacement, getSupplementaryFigures } from "@/data/figures";
import { additionalFindings } from "@/data/findings";
import { limitations } from "@/data/limitations";
import { mainResultsRows } from "@/data/mainResultsTable";
import { paperSectionMap } from "@/data/paperMapping";
import { resultShowcase } from "@/data/resultsShowcase";
import { heroLinks, navItems, overviewAbstract, overviewHighlights, siteConfig } from "@/data/site";
import { heroMetrics } from "@/data/stats";
import {
  benchmarkFacts,
  constructionPipeline,
  evaluationPipeline,
  taskCategories,
  whyWebCompass
} from "@/data/tasks";
import { useActiveSection, useScrollProgress } from "@/lib/hooks";

const NAV_SECTION_IDS = ["overview", "design", "method", "results", "figures", "insights", "limitations", "citation"];

export default function HomePage() {
  const activeSection = useActiveSection(NAV_SECTION_IDS);
  const progress = useScrollProgress();

  const overviewFigure = getFiguresByPlacement("overview")[0];
  const benchmarkFigures = getFiguresByPlacement("benchmark");
  const methodFigures = getFiguresByPlacement("method");
  const resultFigures = getFiguresByPlacement("results");
  const supplementaryFigures = getSupplementaryFigures();

  const benchmarkLead = benchmarkFigures.find((item) => item.priority === "primary") ?? benchmarkFigures[0];
  const methodLead = methodFigures.find((item) => item.priority === "primary") ?? methodFigures[0];
  const methodSupporting = methodFigures.filter((item) => item.id !== methodLead?.id && item.hasRealAsset);

  return (
    <main className="relative bg-grid">
      <Navbar items={navItems} activeSection={activeSection} title={siteConfig.name} progress={progress} />

      <HeroSection
        title={siteConfig.title}
        subtitle={siteConfig.subtitle}
        tagline={siteConfig.tagline}
        authors={siteConfig.authors}
        affiliations={siteConfig.affiliations}
        contacts={siteConfig.contacts}
        links={heroLinks}
        arxivBadge={siteConfig.links.arxivBadge}
        metrics={heroMetrics}
      />

      <section id="results-preview" className="scroll-mt-24 py-10 md:py-14">
        <div className="mx-auto w-full max-w-[1480px] px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="Main Results"
            title="Model Comparison Across Task Types and Dimensions"
            description="The principal benchmark table is moved forward for faster model comparison. Higher scores are encoded with stronger color intensity."
          />
          <PaperSourceNote text={paperSectionMap.findings} />
          <MainResultsTable rows={mainResultsRows} />
        </div>
      </section>

      <AbstractSection
        abstract={overviewAbstract}
        highlights={overviewHighlights}
        sourceNote={paperSectionMap.overview}
      />
      {overviewFigure ? (
        <div className="container -mt-8 mb-10">
          <InlineFigureSpotlight figure={overviewFigure} />
        </div>
      ) : null}

      <SectionContainer id="design">
        <SectionHeading
          eyebrow="Benchmark Design"
          title="Unified Multimodal Benchmark Across the Development Lifecycle"
          description="WebCompass integrates modalities, task types, and realistic engineering constraints into one coherent benchmark design."
        />
        <PaperSourceNote text={paperSectionMap.benchmark} />
        {benchmarkLead ? (
          <div className="mb-8">
            <InlineFigureSpotlight figure={benchmarkLead} />
          </div>
        ) : null}

        <OverviewMatrix tasks={taskCategories} whyItems={whyWebCompass} />

        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle>Benchmark Scale</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">{benchmarkFacts.scale}</CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Difficulty Distribution</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {benchmarkFacts.difficulty.join(" / ")}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Generation Taxonomy</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {benchmarkFacts.generationDomains} application domains
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Evaluation Dimensions</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">Execution / Interactivity / Aesthetics</CardContent>
          </Card>
        </div>

        <div className="mt-4 rounded-xl border border-border/70 bg-card/60 p-4 text-xs text-muted-foreground md:text-sm">
          Task counts: Text-Guided Generation ({benchmarkFacts.taskCounts.textGuidedGeneration}), Vision-Guided Generation ({benchmarkFacts.taskCounts.visionGuidedGeneration}), Video-Guided Generation ({benchmarkFacts.taskCounts.videoGuidedGeneration}), Text-Guided Editing ({benchmarkFacts.taskCounts.textGuidedEditing}), Vision-Guided Editing ({benchmarkFacts.taskCounts.visionGuidedEditing}), Diagnostic Repair ({benchmarkFacts.taskCounts.diagnosticRepair}), Visual-Diagnostic Repair ({benchmarkFacts.taskCounts.visualDiagnosticRepair}).
        </div>

        <div className="mt-12">
          <SectionHeading
            eyebrow="Benchmark Comparison"
            title="Coverage Against Prior Benchmarks"
            description="Values are aligned to Table 1 in the paper."
          />
          <BenchmarkComparisonTable rows={comparisonRows} />
        </div>
      </SectionContainer>

      <SectionContainer id="method">
        <SectionHeading
          eyebrow="Method / Pipeline"
          title="From Data Construction to Task-aware Evaluation"
          description="WebCompass evaluates different task families with tailored judging paradigms while preserving shared dimensions."
        />
        <PaperSourceNote text={paperSectionMap.methodology} />

        <div className="mb-10">
          <MethodFlow />
        </div>

        {methodLead ? (
          <div className="mb-8">
            <InlineFigureSpotlight figure={methodLead} />
          </div>
        ) : null}

        {methodSupporting.length > 0 ? (
          <div className="mb-10 grid gap-5 lg:grid-cols-2">
            {methodSupporting.map((figure) => (
              <InlineFigureCard key={figure.id} figure={figure} />
            ))}
          </div>
        ) : null}

        <h3 className="mb-4 text-xl font-semibold">Data Construction Pipeline</h3>
        <PipelineSection steps={constructionPipeline} />

        <h3 className="mb-4 mt-12 text-xl font-semibold">Evaluation Paradigms</h3>
        <EvaluationSection steps={evaluationPipeline} />
      </SectionContainer>

      <SectionContainer id="results">
        <SectionHeading
          eyebrow="Experimental Results"
          title="Figure-driven Results on Web Coding Agent Evaluation"
          description="Representative result figures from the experiments section."
        />
        <PaperSourceNote text={paperSectionMap.findings} />
        <ResultsShowcase figures={resultFigures} items={resultShowcase} />
      </SectionContainer>

      <SectionContainer id="figures">
        <SectionHeading
          eyebrow="Additional Figures"
          title="Supplementary Figures Referenced in the Paper"
          description="Secondary figures not emphasized above are collected here for completeness."
        />
        <PaperSourceNote text={paperSectionMap.figures} />
        <FiguresGallery figures={supplementaryFigures} />
      </SectionContainer>

      <SectionContainer id="insights">
        <SectionHeading
          eyebrow="Insights"
          title="Key Takeaways for Web Coding Agent Development"
          description="Interpretation-focused insights distilled from result trends and error analyses."
        />
        <InsightsSection findings={additionalFindings} />
      </SectionContainer>

      <SectionContainer id="limitations">
        <SectionHeading
          eyebrow="Limitations"
          title="Scope, Constraints, and Future Directions"
          description="Limitations are presented to clarify scope and inform follow-up benchmark design."
        />
        <PaperSourceNote text={paperSectionMap.discussion} />
        <LimitationsSection items={limitations} />

        <div className="mt-12">
          <SectionHeading
            eyebrow="Conclusion"
            title="Toward More Faithful Evaluation of Web Coding Agents"
            description="WebCompass emphasizes realistic, multimodal, and lifecycle-aware evaluation for future research."
          />
          <ConclusionSection
            text="WebCompass unifies multimodal inputs and lifecycle tasks under evidence-grounded evaluation, positioning web coding agents as holistic builders of user-facing experiences rather than code-only generators."
          />
        </div>
      </SectionContainer>

      <SectionContainer id="citation">
        <SectionHeading
          eyebrow="Citation"
          title="Use and Extend WebCompass"
          description="If WebCompass is useful for your research, please cite the paper and explore project resources."
        />
        <PaperSourceNote text={paperSectionMap.citation} />
        <CitationSection
          bibtex={citation.bibtex}
          resources={[
            { label: "Paper", href: siteConfig.links.paper },
            { label: "GitHub", href: siteConfig.links.github },
            { label: "Hugging Face", href: siteConfig.links.huggingface },
            { label: "Dataset", href: siteConfig.links.dataset }
          ]}
        />
      </SectionContainer>

      <Footer projectName={siteConfig.name} builtWith={siteConfig.builtWith} />
      <BackToTop />
    </main>
  );
}


