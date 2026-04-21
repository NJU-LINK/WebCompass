type ConclusionSectionProps = {
  text: string;
};

export function ConclusionSection({ text }: ConclusionSectionProps) {
  return (
    <div className="mx-auto max-w-4xl rounded-2xl border border-border/70 bg-card/70 p-8 text-center md:p-10">
      <p className="text-pretty text-lg leading-relaxed text-muted-foreground">{text}</p>
    </div>
  );
}