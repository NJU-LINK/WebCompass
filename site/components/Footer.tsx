type FooterProps = {
  projectName: string;
  builtWith: string;
};

export function Footer({ projectName, builtWith }: FooterProps) {
  return (
    <footer className="border-t border-border/60 py-10">
      <div className="container flex flex-col items-start justify-between gap-2 text-sm text-muted-foreground md:flex-row md:items-center">
        <p>{projectName} ? 2026. All rights reserved.</p>
        <p>Built with {builtWith}.</p>
        <p>This website is inspired by modern academic project pages.</p>
      </div>
    </footer>
  );
}