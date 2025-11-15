"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import NavBar from "@/components/NavBar";
import { useStoredUser } from "@/hooks/useStoredUser";
import { apiPost } from "@/lib/api";

const TOPICS = [
  { id: "add_sub", label: "整式加减", hint: "专注合并同类项，括号要展开再合并" },
  { id: "mul_div", label: "整式乘除", hint: "先约掉公因子，再整理次数" },
  { id: "factorization", label: "因式分解", hint: "留意完全平方、平方差和分组法" },
] as const;

const DIFFICULTIES = [
  { id: "basic", label: "低级", desc: "0-33 分：一次或二次、项数较少" },
  { id: "intermediate", label: "中级", desc: "34-66 分：项数与次数更高" },
  { id: "advanced", label: "高级", desc: "67-100 分：复杂系数或嵌套" },
] as const;

type QuestionResponse = {
  questionId: string;
  topic: string;
  difficultyLevel: string;
  expressionText: string;
  difficultyScore: number;
};

type CheckAnswerResponse = {
  isCorrect: boolean;
  difficultyScore: number;
  scoreChange: number;
  newTotalScore: number;
  attemptCount: number;
};

export default function PracticePage() {
  const router = useRouter();
  const { user, writeUser, updateUserScore } = useStoredUser();
  const [selectedTopic, setSelectedTopic] = useState<(typeof TOPICS)[number]["id"]>("add_sub");
  const [selectedDifficulty, setSelectedDifficulty] = useState<(typeof DIFFICULTIES)[number]["id"]>("basic");
  const [question, setQuestion] = useState<QuestionResponse | null>(null);
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attemptCount, setAttemptCount] = useState(0);
  const [status, setStatus] = useState<"idle" | "correct" | "exhausted">("idle");
  const [submitting, setSubmitting] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const logout = useCallback(() => {
    writeUser(null);
    router.replace("/");
  }, [router, writeUser]);

  useEffect(() => {
    if (!user) {
      router.replace("/");
    }
  }, [user, router]);

  const fetchQuestion = useCallback(async () => {
    if (!user) return;
    setLoadingQuestion(true);
    setError(null);
    setFeedback(null);
    setAttemptCount(0);
    setStatus("idle");
    setAnswer("");
    try {
      const payload = await apiPost<QuestionResponse>("/api/generate_question", {
        userId: user.userId,
        topic: selectedTopic,
        difficultyLevel: selectedDifficulty,
      });
      setQuestion(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取题目失败");
    } finally {
      setLoadingQuestion(false);
    }
  }, [selectedDifficulty, selectedTopic, user]);

  useEffect(() => {
    if (user) {
      fetchQuestion();
    }
  }, [user, fetchQuestion]);

  const handleSubmit = async () => {
    if (!user || !question || !answer.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await apiPost<CheckAnswerResponse>("/api/check_answer", {
        userId: user.userId,
        questionId: question.questionId,
        expressionText: question.expressionText,
        topic: question.topic,
        difficultyLevel: question.difficultyLevel,
        userAnswer: answer,
      });
      const remaining = Math.max(0, 3 - result.attemptCount);
      setFeedback(
        result.isCorrect
          ? `答对啦！得分 ${result.scoreChange > 0 ? `+${result.scoreChange}` : result.scoreChange}`
          : `未通过，积分 ${result.scoreChange}. 还剩 ${remaining} 次机会`
      );
      setAttemptCount(result.attemptCount);
      if (result.isCorrect) {
        setStatus("correct");
      } else if (result.attemptCount >= 3) {
        setStatus("exhausted");
      }
      updateUserScore(result.newTotalScore);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败，请稍后再试");
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = !!question && status !== "correct" && !submitting && !!answer.trim();
  const canGoNext = status === "correct" || attemptCount >= 3;
  const currentTopic = useMemo(() => TOPICS.find((item) => item.id === selectedTopic), [selectedTopic]);
  const instructions = `输入规则：使用 x 作为未知数，^ 表示乘方（如 x^2），/ 表示分数（如 1/2），请勿输入空格。`;

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50">
        <NavBar user={null} onLogout={logout} />
        <div className="mx-auto max-w-4xl px-4 py-10 text-gray-600">正在加载...</div>
      </div>
    );
  }

  const filterPanel = (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase text-gray-500">题型</p>
        <div className="mt-3 flex flex-col gap-2">
          {TOPICS.map((topic) => (
            <button
              key={topic.id}
              onClick={() => {
                setSelectedTopic(topic.id);
                setShowFilters(false);
              }}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                selectedTopic === topic.id
                  ? "border-purple-500 bg-purple-50 text-purple-700"
                  : "border-gray-200 hover:border-purple-200"
              }`}
            >
              <p className="text-sm font-semibold">{topic.label}</p>
              <p className="text-xs text-gray-500">{topic.hint}</p>
            </button>
          ))}
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase text-gray-500">难度</p>
        <div className="mt-3 flex flex-col gap-2">
          {DIFFICULTIES.map((level) => (
            <button
              key={level.id}
              onClick={() => {
                setSelectedDifficulty(level.id);
                setShowFilters(false);
              }}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                selectedDifficulty === level.id
                  ? "border-orange-500 bg-orange-50 text-orange-600"
                  : "border-gray-200 hover:border-orange-200"
              }`}
            >
              <p className="text-sm font-semibold">{level.label}</p>
              <p className="text-xs text-gray-500">{level.desc}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar user={user} onLogout={logout} />
      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 lg:flex-row">
        <aside className="hidden w-72 flex-shrink-0 rounded-2xl bg-white p-6 shadow-sm lg:block">
          {filterPanel}
        </aside>
        <div className="lg:hidden">
          <button
            onClick={() => setShowFilters((prev) => !prev)}
            className="w-full rounded-2xl border border-purple-200 bg-white px-4 py-3 text-sm font-semibold text-purple-700"
          >
            {showFilters ? "收起筛选" : "展开筛选"}
          </button>
          {showFilters && <div className="mt-4 rounded-2xl bg-white p-4 shadow-sm">{filterPanel}</div>}
        </div>
        <section className="flex-1 rounded-3xl bg-white p-6 shadow-md">
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
            <span className="rounded-full bg-purple-100 px-3 py-1 text-purple-700">
              {currentTopic?.label}
            </span>
            <span className="rounded-full bg-orange-100 px-3 py-1 text-orange-700">
              {DIFFICULTIES.find((item) => item.id === selectedDifficulty)?.label} 难度 ·
              评分 {question?.difficultyScore ?? "--"}
            </span>
            {feedback && (
              <span
                className={`rounded-full px-3 py-1 ${
                  status === "correct" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {feedback}
              </span>
            )}
          </div>
          <div className="mt-6 rounded-2xl bg-slate-50 p-6 text-gray-800">
            {loadingQuestion && <p>正在为你准备新题目...</p>}
            {!loadingQuestion && question && (
              <>
                <p className="text-sm uppercase text-gray-500">当前表达式</p>
                <p className="mt-2 text-2xl font-semibold text-gray-900">{question.expressionText}</p>
              </>
            )}
          </div>
          <p className="mt-4 text-sm text-gray-500">{instructions}</p>
          <div className="mt-6 space-y-3">
            <textarea
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              rows={3}
              className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-base focus:border-purple-500 focus:outline-none"
              placeholder="例如 (x+2)^2 - 3x"
              disabled={status === "correct"}
            />
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
              <span>已用 {attemptCount} / 3 次机会</span>
              {status === "correct" && <span className="text-green-600">本题已完成，可进行下一题</span>}
              {status === "exhausted" && <span className="text-red-500">机会用尽，请下一题</span>}
            </div>
          </div>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          <div className="mt-6 flex flex-wrap gap-4">
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="rounded-2xl bg-purple-600 px-8 py-3 text-white shadow-lg transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "判分中..." : "提交答案"}
            </button>
            <button
              onClick={fetchQuestion}
              disabled={!canGoNext}
              className="rounded-2xl border border-gray-200 px-8 py-3 text-gray-700 transition hover:border-purple-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              下一题
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
