"use client";

import { useEffect, useState } from "react";

const ACTIVE_OFFSET = 140;
const TOP_TIE_EPSILON = 0.5;

function byDocumentTop(a: HTMLElement, b: HTMLElement) {
  return a.offsetTop - b.offsetTop;
}

function pickClosestToViewportTop(sections: HTMLElement[], offset: number) {
  let closestId = sections[0]?.id ?? "";
  let bestDistance = Number.POSITIVE_INFINITY;
  let bestTop = Number.POSITIVE_INFINITY;

  for (const section of sections) {
    const top = section.getBoundingClientRect().top;
    const distance = Math.abs(top - offset);

    if (
      distance < bestDistance - TOP_TIE_EPSILON ||
      (Math.abs(distance - bestDistance) <= TOP_TIE_EPSILON && top < bestTop)
    ) {
      bestDistance = distance;
      bestTop = top;
      closestId = section.id;
    }
  }

  return closestId;
}

function pickActiveCanonicalSection(sections: HTMLElement[], intersectingIds: Set<string>, offset: number) {
  const sortedSections = [...sections].sort(byDocumentTop);
  const atPageBottom = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4;

  if (atPageBottom) {
    return sortedSections[sortedSections.length - 1]?.id ?? "";
  }

  const intersectingSections = sortedSections.filter((section) => intersectingIds.has(section.id));
  if (intersectingSections.length > 0) {
    // Prefer the visible canonical section whose anchor is closest to the sticky-header line.
    return pickClosestToViewportTop(intersectingSections, offset);
  }

  const scrollAnchor = window.scrollY + offset;
  const reachedSections = sortedSections.filter((section) => section.offsetTop <= scrollAnchor);

  if (reachedSections.length > 0) {
    return reachedSections[reachedSections.length - 1].id;
  }

  return pickClosestToViewportTop(sortedSections, offset);
}

export function useActiveSection(sectionIds: string[]) {
  const [activeId, setActiveId] = useState(sectionIds[0] ?? "");

  useEffect(() => {
    const canonicalSections = sectionIds
      .map((id) => document.getElementById(id))
      .filter((node): node is HTMLElement => Boolean(node));

    if (canonicalSections.length === 0) return;

    const intersectingIds = new Set<string>();

    const updateActive = () => {
      const next = pickActiveCanonicalSection(canonicalSections, intersectingIds, ACTIVE_OFFSET);
      setActiveId((prev) => {
        if (prev === next) return prev;
        window.history.replaceState(null, "", `#${next}`);
        return next;
      });
    };

    updateActive();

    const observer = new IntersectionObserver(
      () => {
        canonicalSections.forEach((section) => {
          const rect = section.getBoundingClientRect();
          const isVisible = rect.bottom > 0 && rect.top < window.innerHeight;
          if (isVisible) {
            intersectingIds.add(section.id);
          } else {
            intersectingIds.delete(section.id);
          }
        });
        updateActive();
      },
      {
        root: null,
        // Keep tracking stable around the sticky header region.
        rootMargin: "-25% 0px -65% 0px",
        threshold: [0, 0.1, 0.25, 0.5, 1]
      }
    );

    canonicalSections.forEach((section) => observer.observe(section));
    window.addEventListener("scroll", updateActive, { passive: true });
    window.addEventListener("resize", updateActive);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", updateActive);
      window.removeEventListener("resize", updateActive);
    };
  }, [sectionIds]);

  return activeId;
}

export function useScrollProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      const next = total > 0 ? (window.scrollY / total) * 100 : 0;
      setProgress(Math.min(100, Math.max(0, next)));
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return progress;
}
