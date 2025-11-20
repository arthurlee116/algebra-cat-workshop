"use client";

import { useEffect, useState, useCallback } from "react";
import { apiGet } from "@/lib/api";

interface RecentQuestion {
  questionId: string;
  expressionText: string;
  createdAt: string;
}

interface RecentQuestionsResponse {
  questions: RecentQuestion[];
}

export function useRecentQuestions(userId?: number, refreshKey: number = 0) {
  const [data, setData] = useState<RecentQuestionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (typeof userId !== "number") {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<RecentQuestionsResponse>(`/api/users/${userId}/recent_questions`);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取最近题目失败");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (typeof userId !== "number") {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    fetchData();
  }, [userId, refreshKey, fetchData]);

  return { data, loading, error, refetch: fetchData };
}
