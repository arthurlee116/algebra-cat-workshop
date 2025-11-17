"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import NavBar from "@/components/NavBar";
import LatexExpression from "@/components/LatexExpression";
import { useStoredUser } from "@/hooks/useStoredUser";
import { apiPost } from "@/lib/api";

const TOPICS = [
  { id: "add_sub", label: "整式加减", hint: "专注合并同类项，括号要展开再合并" },
  { id: "mul_div", label: "整式乘除", hint: "先约掉公因子，再整理次数" },
  { id: "mixed_ops", label: "整式加减乘除混合", hint: "加减乘除综合，先约分再展开合并同类项" },
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
  expressionLatex: string;
  difficultyScore: number;
};

type CheckAnswerResponse = {
  isCorrect: boolean;
  difficultyScore: number;
  scoreChange: number;
  newTotalScore: number;
  attemptCount: number;
  solutionExpression?: string;
};

export default function PracticePage() {
  const router = useRouter();
  const { user, writeUser, updateUserScore } = useStoredUser();
  const userId = user?.userId;
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
  const [scoreChange, setScoreChange] = useState<number | null>(null);
  const [previousScore, setPreviousScore] = useState<number | null>(null);
  const [solutionExpression, setSolutionExpression] = useState<string | null>(null);
  const [inputError, setInputError] = useState(false);
  const answerInputRef = useRef<HTMLTextAreaElement | null>(null);
  const shakeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggerInputError = useCallback(() => {
    if (shakeTimeoutRef.current) {
      clearTimeout(shakeTimeoutRef.current);
    }
    setInputError(true);
    answerInputRef.current?.focus();
    shakeTimeoutRef.current = setTimeout(() => {
      setInputError(false);
      shakeTimeoutRef.current = null;
    }, 600);
  }, []);

  useEffect(() => {
    return () => {
      if (shakeTimeoutRef.current) {
        clearTimeout(shakeTimeoutRef.current);
      }
    };
  }, []);

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
    if (!userId) return;
    setLoadingQuestion(true);
    setError(null);
    setFeedback(null);
    setAttemptCount(0);
    setStatus("idle");
    setAnswer("");
    // 清除之前的反馈状态
    setScoreChange(null);
    setPreviousScore(null);
    setSolutionExpression(null);
    try {
      const payload = await apiPost<QuestionResponse>("/api/generate_question", {
        userId,
        topic: selectedTopic,
        difficultyLevel: selectedDifficulty,
      });
      setQuestion(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取题目失败");
    } finally {
      setLoadingQuestion(false);
    }
  }, [selectedDifficulty, selectedTopic, userId]);

  useEffect(() => {
    if (userId) {
      fetchQuestion();
    }
  }, [userId, fetchQuestion]);

  const handleSubmit = async () => {
    if (!user || !question || !answer.trim()) return;
    setSubmitting(true);
    setError(null);
    setPreviousScore(user.total_score);
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

      // 设置积分变化信息
      setScoreChange(result.scoreChange);

      // 如果有标准答案，保存它
      if (result.solutionExpression) {
        setSolutionExpression(result.solutionExpression);
      }

      // 构建详细的反馈信息
      let feedbackMessage = "";
      if (result.isCorrect) {
        feedbackMessage = `🎉 答对了！获得 ${result.scoreChange > 0 ? `+${result.scoreChange}` : result.scoreChange} 分`;
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
      } else {
        triggerInputError();
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
  const instructions =
    "输入规则：按题目给出的字母作为未知数（可能包含 x、y、z），^ 表示乘方（如 x^2），/ 表示分数（如 1/2），乘号可省略，空格可写可不写。上方蓝底区域是卷面写法，下面灰底示例提醒你如何键盘输入。";

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
              <p className="text-sm font-semibold text-gray-900">{topic.label}</p>
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
              <p className="text-sm font-semibold text-gray-900">{level.label}</p>
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
              <div className={`rounded-xl px-4 py-3 text-sm font-medium ${
                status === "correct" ? "bg-green-50 border border-green-200 text-green-800" : "bg-yellow-50 border border-yellow-200 text-yellow-800"
              }`}>
                <p className="font-semibold">{feedback}</p>
                {scoreChange !== null && previousScore !== null && user && (
                  <p className="mt-1 text-xs font-normal">
                    总积分: {previousScore} → {user.total_score}
                    {scoreChange !== 0 && (
                      <span className={`ml-2 font-semibold ${scoreChange > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ({scoreChange > 0 ? '+' : ''}{scoreChange})
                      </span>
                    )}
                  </p>
                )}
              </div>
            )}
          </div>
          <div className="mt-6 rounded-2xl bg-slate-50 p-6 text-gray-800">
            {loadingQuestion && <p>正在为你准备新题目...</p>}
            {!loadingQuestion && question && (
              <>
                <p className="text-sm uppercase text-gray-500">当前表达式</p>
                <div className="mt-3 space-y-4">
                  <div className="rounded-2xl border border-purple-100 bg-white/70 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-purple-500">卷面展示</p>
                    <LatexExpression expression={question.expressionLatex} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">输入示例</p>
                    <p className="mt-1 rounded-xl border border-slate-200 bg-white px-4 py-2 font-mono text-lg font-semibold text-gray-900">
                      {question.expressionText}
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
          <p className="mt-4 text-sm text-gray-500">{instructions}</p>
          <div className="mt-6 space-y-3">
            <textarea
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              rows={3}
              ref={answerInputRef}
              className={`w-full rounded-2xl border px-4 py-3 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none transition ${
                inputError ? "border-red-500 focus:border-red-500 shake-input" : "border-gray-200 focus:border-purple-500"
              }`}
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

          {/* 答案提示 - 3次机会用尽时显示 */}
          {status === "exhausted" && solutionExpression && (
            <div className="mt-4 rounded-xl bg-blue-50 border border-blue-200 p-4">
              <p className="font-semibold text-blue-900 mb-2">💡 正确答案：</p>
              <p className="text-blue-800 font-mono text-sm bg-white px-3 py-2 rounded-lg border border-blue-300">
                {solutionExpression}
              </p>
              <p className="text-blue-700 text-xs mt-2">
                提示：因式分解时要注意符号的正确性，常见错误包括：
              </p>
              <ul className="text-blue-600 text-xs mt-1 ml-4 list-disc">
                <li>符号错误（如 + 写成 -）</li>
                <li>变量错误（如 x 写成 z）</li>
                <li>括号展开错误</li>
              </ul>
            </div>
          )}

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
