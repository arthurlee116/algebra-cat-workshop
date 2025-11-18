"use client";

import { useEffect, useRef } from "react";

type KatexModule = typeof import("katex");

let katexPromise: Promise<KatexModule> | null = null;

function loadKatex() {
  if (!katexPromise) {
    katexPromise = import("katex");
  }
  return katexPromise;
}

type LatexExpressionProps = {
  expression: string;
  displayMode?: boolean;
};

export default function LatexExpression({ expression, displayMode = true }: LatexExpressionProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    element.textContent = expression;

    let cancelled = false;
    loadKatex()
      .then((katex) => {
        if (cancelled || !containerRef.current) return;
        katex.render(expression, containerRef.current, {
          throwOnError: false,
          displayMode,
          strict: "warn",
        });
      })
      .catch((error) => {
        console.error("渲染 LaTeX 失败", error);
      });

    return () => {
      cancelled = true;
    };
  }, [expression, displayMode]);

  return (
    <div
      ref={containerRef}
      className="mt-2 overflow-auto rounded-xl bg-purple-50/60 px-3 py-2 text-base text-gray-900"
      aria-label="卷面形式"
    />
  );
}
