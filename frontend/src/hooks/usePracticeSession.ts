import { useCallback, useState } from "react";

import { apiPost } from "@/lib/api";

export type PracticeStatus = "idle" | "correct" | "exhausted";

export type PracticeQuestion = {
  questionId: string;
  topic: string;
  difficultyLevel: string;
  expressionText: string;
  expressionLatex: string;
  difficultyScore: number;
};

export type PracticeAnswerResult = {
  isCorrect: boolean;
  difficultyScore: number;
  scoreChange: number;
  newTotalScore: number;
  attemptCount: number;
  solutionExpression?: string;
};

type UserShape = {
  userId: number;
  total_score: number;
};

type UsePracticeSessionParams = {
  user: UserShape | null;
  topic: string;
  difficulty: string;
  onScoreUpdate: (score: number) => void;
};

export function usePracticeSession({
  user,
  topic,
  difficulty,
  onScoreUpdate,
}: UsePracticeSessionParams) {
  const [question, setQuestion] = useState<PracticeQuestion | null>(null);
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attemptCount, setAttemptCount] = useState(0);
  const [status, setStatus] = useState<PracticeStatus>("idle");
  const [submitting, setSubmitting] = useState(false);
  const [scoreChange, setScoreChange] = useState<number | null>(null);
  const [previousScore, setPreviousScore] = useState<number | null>(null);
  const [solutionExpression, setSolutionExpression] = useState<string | null>(null);
  const [recentRefreshKey, setRecentRefreshKey] = useState(0);

  const fetchQuestion = useCallback(async () => {
    if (!user?.userId) return false;
    setLoadingQuestion(true);
    setError(null);
    setFeedback(null);
    setAttemptCount(0);
    setStatus("idle");
    setScoreChange(null);
    setPreviousScore(null);
    setSolutionExpression(null);

    try {
      const payload = await apiPost<PracticeQuestion>("/api/generate_question", {
        userId: user.userId,
        topic,
        difficultyLevel: difficulty,
      });
      setQuestion(payload);
      setRecentRefreshKey((prev) => prev + 1);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取题目失败");
      return false;
    } finally {
      setLoadingQuestion(false);
    }
  }, [difficulty, topic, user?.userId]);

  const submitAnswer = useCallback(
    async (answer: string): Promise<PracticeAnswerResult | null> => {
      if (!user || !question) return null;
      setSubmitting(true);
      setError(null);
      setPreviousScore(user.total_score);

      try {
        const result = await apiPost<PracticeAnswerResult>("/api/check_answer", {
          userId: user.userId,
          questionId: question.questionId,
          expressionText: question.expressionText,
          topic: question.topic,
          difficultyLevel: question.difficultyLevel,
          userAnswer: answer,
        });

        const remaining = Math.max(0, 3 - result.attemptCount);
        setScoreChange(result.scoreChange);
        if (result.solutionExpression) {
          setSolutionExpression(result.solutionExpression);
        }

        let feedbackMessage = "";
        if (result.isCorrect) {
          const delta = result.scoreChange > 0 ? `+${result.scoreChange}` : result.scoreChange;
          feedbackMessage = `🎉 答对了！获得 ${delta} 分`;
        } else {
          const impact = result.scoreChange < 0 ? `扣除 ${Math.abs(result.scoreChange)} 分` : "不扣分";
          feedbackMessage = `❌ 答案错误，${impact}。还剩 ${remaining} 次机会`;
        }

        setFeedback(feedbackMessage);
        setAttemptCount(result.attemptCount);
        if (result.isCorrect) {
          setStatus("correct");
        } else if (result.attemptCount >= 3) {
          setStatus("exhausted");
        }
        onScoreUpdate(result.newTotalScore);

        try {
          await apiPost("/api/history", {
            user_id: user.userId,
            question_text: question.expressionText,
            user_answer: answer,
            score: result.scoreChange,
            correct_answer: result.solutionExpression || null,
          });
        } catch (historyErr) {
          console.error("Failed to save history", historyErr);
        }

        return result;
      } catch (err) {
        setError(err instanceof Error ? err.message : "提交失败，请稍后再试");
        return null;
      } finally {
        setSubmitting(false);
      }
    },
    [onScoreUpdate, question, user],
  );

  return {
    question,
    loadingQuestion,
    feedback,
    error,
    attemptCount,
    status,
    submitting,
    scoreChange,
    previousScore,
    solutionExpression,
    recentRefreshKey,
    fetchQuestion,
    submitAnswer,
  };
}

export default usePracticeSession;
