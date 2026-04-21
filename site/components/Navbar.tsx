"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { NavItem } from "@/lib/types";
import { cn } from "@/lib/utils";

type NavbarProps = {
  items: NavItem[];
  activeSection: string;
  title: string;
  progress: number;
};

export function Navbar({ items, activeSection, title, progress }: NavbarProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="container flex h-16 items-center justify-between">
          <a href="#top" className="text-sm font-semibold tracking-wide text-foreground md:text-base">
            {title}
          </a>
          <nav className="hidden items-center gap-1 md:flex">
            {items.map((item) => {
              const isActive = activeSection && item.href === `#${activeSection}`;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-md px-3 py-2 text-sm transition-colors",
                    isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {item.label}
                </a>
              );
            })}
          </nav>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setOpen((v) => !v)}
            className="md:hidden"
            aria-label="Toggle menu"
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
        <div className="h-[2px] w-full bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
        </div>
      </header>
      {open ? (
        <div className="fixed inset-0 z-40 bg-background/95 pt-20 backdrop-blur-lg md:hidden">
          <div className="container flex flex-col gap-2">
            {items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "rounded-lg border border-transparent px-4 py-3 text-base",
                  item.href === `#${activeSection}`
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "text-foreground hover:border-border hover:bg-muted"
                )}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}