"use client";

import { motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";

type SectionHeadingProps = {
  eyebrow?: string;
  title: string;
  description?: string;
};

export function SectionHeading({ eyebrow, title, description }: SectionHeadingProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.45 }}
      className="mx-auto mb-10 max-w-3xl text-center"
    >
      {eyebrow ? <Badge className="mb-3">{eyebrow}</Badge> : null}
      <h2 className="text-balance text-2xl font-semibold tracking-tight text-foreground md:text-4xl">{title}</h2>
      {description ? <p className="mt-4 text-pretty text-muted-foreground md:text-lg">{description}</p> : null}
    </motion.div>
  );
}