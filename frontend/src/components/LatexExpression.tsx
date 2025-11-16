"use client";

import { useEffect, useRef } from "react";

declare global {
  interface Window {
    katex?: {
      render: (expression: string, element: HTMLElement, options?: Record<string, unknown>) => void;
    };
  }
}

type LatexExpressionProps = {
  expression: string;
  displayMode?: boolean;
};

export default function LatexExpression({ expression, displayMode = true }: LatexExpressionProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    if (typeof window === "undefined") return;

    if (window.katex?.render) {
      try {
        window.katex.render(expression, containerRef.current, {
          throwOnError: false,
          displayMode,
          strict: "warn",
        });
        return;
      } catch (error) {
        console.error("渲染 LaTeX 失败", error);
      }
    }
    containerRef.current.textContent = expression;
  }, [expression, displayMode]);

  return (
    <div
      ref={containerRef}
      className="mt-2 overflow-auto rounded-xl bg-purple-50/60 px-3 py-2 text-base text-gray-900"
      aria-label="卷面形式"
    />
  );
}
