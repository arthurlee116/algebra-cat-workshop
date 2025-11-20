"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiPost } from "@/lib/api";

type DifficultyLevel = "basic" | "intermediate" | "advanced";
type Topic = "add_sub" | "mul_div" | "poly_ops" | "factorization" | "mixed_ops";

export type BatchQuestion = {
  questionId: string;
  topic: Topic;
  difficultyLevel: DifficultyLevel;
  expressionText: string;
  expressionLatex: string;
  difficultyScore: number;
  solutionExpression: string;
};

export type BatchResponse = { questions: BatchQuestion[] };

export type BatchRequest = { count: number; difficulty?: DifficultyLevel };

export function useBatchQuestions(initialParams: BatchRequest) {
  const { count, difficulty } = initialParams;
  const memoizedParams = useMemo(() => ({ count, difficulty }), [count, difficulty]);

  const [questions, setQuestions] = useState<BatchQuestion[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = useCallback(async (params: BatchRequest = memoizedParams) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<BatchResponse>("/api/questions/batch", params);
      setQuestions(response.questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch questions");
    } finally {
      setLoading(false);
    }
  }, [memoizedParams]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  return { questions, loading, error, refetch: fetchQuestions };
}

/*
Minimal usage example:

"use client"
import { useBatchQuestions } from "@/hooks/useBatchQuestions";

export default function BatchDemo() {
  const { questions, loading } = useBatchQuestions({ count: 5 });
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      {questions?.map((q) => (
        <p key={q.questionId}>{q.expressionText}</p>
      ))}
    </div>
  );
}
*/
