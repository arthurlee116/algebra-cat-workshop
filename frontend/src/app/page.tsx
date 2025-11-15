"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useStoredUser } from "@/hooks/useStoredUser";
import { StoredUser } from "@/lib/userStorage";

export default function LoginPage() {
  const router = useRouter();
  const { writeUser } = useStoredUser();
  const [form, setForm] = useState({
    chinese_name: "",
    english_name: "",
    class_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<{
        userId: number;
        chinese_name: string;
        english_name: string;
        class_name: string;
        total_score: number;
      }>("/api/login", form);
      const stored: StoredUser = {
        userId: response.userId,
        chinese_name: response.chinese_name,
        english_name: response.english_name,
        class_name: response.class_name,
        total_score: response.total_score,
      };
      writeUser(stored);
      router.push("/practice");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败，请稍后再试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white px-4 py-12">
      <div className="mx-auto flex max-w-5xl flex-col gap-12 lg:flex-row">
        <section className="flex-1">
          <h1 className="text-4xl font-bold text-gray-900">上海七年级整式练习站</h1>
          <p className="mt-4 text-lg text-gray-600">
            自动生成整式加减、乘除与因式分解题目，带难度评估、智能判分与虚拟猫咪激励。填写真实姓名与班级即可开始。
          </p>
          <ul className="mt-8 space-y-4 text-gray-700">
            <li>· 随机题目，自动匹配对应难度区间</li>
            <li>· SymPy 精确判断等价表达式，支持 x、^、/ 输入</li>
            <li>· 获取积分喂养猫咪，见证四种成长形态</li>
          </ul>
        </section>
        <section className="flex-1 rounded-2xl bg-white p-8 shadow-lg">
          <h2 className="text-2xl font-semibold text-purple-700">登录 / 创建学生档案</h2>
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm font-medium text-gray-700">
              中文姓名
              <input
                type="text"
                required
                value={form.chinese_name}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, chinese_name: event.target.value }))
                }
                className="mt-1 w-full rounded-xl border border-gray-200 px-4 py-2 focus:border-purple-500 focus:outline-none"
              />
            </label>
            <label className="block text-sm font-medium text-gray-700">
              英文名 / 拼音
              <input
                type="text"
                required
                value={form.english_name}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, english_name: event.target.value }))
                }
                className="mt-1 w-full rounded-xl border border-gray-200 px-4 py-2 focus:border-purple-500 focus:outline-none"
              />
            </label>
            <label className="block text-sm font-medium text-gray-700">
              班级（例如 7-3）
              <input
                type="text"
                required
                value={form.class_name}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, class_name: event.target.value }))
                }
                className="mt-1 w-full rounded-xl border border-gray-200 px-4 py-2 focus:border-purple-500 focus:outline-none"
              />
            </label>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-purple-600 px-4 py-3 text-white transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "正在登录..." : "开始练习"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
