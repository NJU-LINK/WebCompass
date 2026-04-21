type PaperSourceNoteProps = {
  text: string;
};

export function PaperSourceNote({ text }: PaperSourceNoteProps) {
  return <p className="mb-6 text-xs text-muted-foreground">{text}</p>;
}