"use client";

import { useState, useEffect } from "react";
import NavBar from "@/components/NavBar";
import { useStoredUser } from "@/hooks/useStoredUser";
import { apiGet } from "@/lib/api";

interface HistoryItem {
  id: number;
  user_id: number;
  question_text: string;
  user_answer: string;
  score: number;
  correct_answer?: string | null;
  created_at: string;
}

export default function HistoryPage() {
  const { user, writeUser } = useStoredUser();
  const [histories, setHistories] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    min_score: "",
    date_from: "",
    date_to: "",
  });

  const userId = user?.userId;
  const logout = () => writeUser(null);

  const fetchHistory = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        user_id: userId.toString(),
        limit: "20",
        offset: "0",
      });
      if (filters.min_score) params.append("min_score", filters.min_score);
      if (filters.date_from) params.append("date_from", filters.date_from);
      if (filters.date_to) params.append("date_to", filters.date_to);
      const data = await apiGet<HistoryItem[]>(`/api/history?${params}`);
      setHistories(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载历史记录失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [userId, filters]);

  const handleFilterChange = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-gray-600">请先登录</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar user={user} onLogout={logout} />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">练习历史</h1>
        <div className="bg-white rounded-3xl p-8 shadow-lg">
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">筛选条件</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input
                type="number"
                placeholder="最低分数"
                value={filters.min_score}
                onChange={(e) => handleFilterChange("min_score", e.target.value)}
                className="rounded-xl border border-gray-200 px-4 py-3 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
              />
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => handleFilterChange("date_from", e.target.value)}
                className="rounded-xl border border-gray-200 px-4 py-3 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
              />
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => handleFilterChange("date_to", e.target.value)}
                className="rounded-xl border border-gray-200 px-4 py-3 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200"
              />
            </div>
          </div>
          {loading ? (
            <div className="text-center text-gray-600">加载中...</div>
          ) : error ? (
            <div className="text-center text-red-500">{error}</div>
          ) : histories.length === 0 ? (
            <div className="text-center text-gray-600">暂无历史记录</div>
          ) : (
            <div className="space-y-4">
              {histories.map((item) => (
                <div
                  key={item.id}
                  className="rounded-xl shadow bg-slate-50 p-8"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      {new Date(item.created_at).toLocaleString()}
                    </div>
                    <div
                      className={`px-2 py-1 text-xs rounded-full ${
                        item.score >= 0
                          ? "bg-green-100 text-green-800 border border-green-200"
                          : "bg-red-100 text-red-800 border border-red-200"
                      }`}
                    >
                      {item.score > 0 ? `+${item.score}` : item.score}
                    </div>
                  </div>
                  <p className="mt-2 text-gray-900 font-semibold truncate">
                    {item.question_text}
                  </p>
                  <p className="mt-1 text-gray-700 mono">
                    {item.user_answer}
                  </p>
                  {item.correct_answer && (
                    <p className="mt-1 text-gray-500 mono">
                      正确答案：{item.correct_answer}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
