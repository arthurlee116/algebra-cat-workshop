import { useState } from 'react';

export type DifficultyLevel = 'basic' | 'intermediate' | 'advanced';

export interface QuestionItem {
  questionId: string;
  topic: string;
  difficultyLevel: string;
  expressionText: string;
  expressionLatex: string;
  difficultyScore: number;
  solutionExpression: string;
}

export interface BatchGenerateResponse {
  questions: QuestionItem[];
}

export interface UseBatchQuestionsReturn {
  questions: QuestionItem[];
  loading: boolean;
  error: string | null;
  fetchQuestions: (count: number, difficulty?: DifficultyLevel) => Promise<void>;
}

export function useBatchQuestions(): UseBatchQuestionsReturn {
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = async (count: number, difficulty?: DifficultyLevel) => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
      const body: { count: number; difficulty?: DifficultyLevel } = { count };
      if (difficulty) {
        body.difficulty = difficulty;
      }

      const res = await fetch(`${baseUrl}/api/questions/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`Error: ${res.statusText}`);
      }

      const data: BatchGenerateResponse = await res.json();
      setQuestions(data.questions);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unknown error');
      }
    } finally {
      setLoading(false);
    }
  };

  return { questions, loading, error, fetchQuestions };
}
