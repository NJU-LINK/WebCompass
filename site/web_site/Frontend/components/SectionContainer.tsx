import { cn } from "@/lib/utils";

type SectionContainerProps = {
  id: string;
  className?: string;
  children: React.ReactNode;
};

export function SectionContainer({ id, className, children }: SectionContainerProps) {
  return (
    <section id={id} className={cn("scroll-mt-24 py-16 md:py-20", className)}>
      <div className="container">{children}</div>
    </section>
  );
}