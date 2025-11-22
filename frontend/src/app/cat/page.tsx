"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { getCatImage, nextStageDiff, stageLabel } from "@/lib/cat";
import useCatData from "@/hooks/useCatData";
import { useStoredUser } from "@/hooks/useStoredUser";

const NavBar = dynamic(() => import("@/components/NavBar"), { ssr: false });

export default function CatPage() {
  const router = useRouter();
  const { user, writeUser, updateUserScore } = useStoredUser();
  const [celebrating, setCelebrating] = useState(false);
  const [highlightFood, setHighlightFood] = useState<string | null>(null);
  const { foods, summary, error, loading, buyingId, buyFood } = useCatData({
    user,
    onScoreUpdate: updateUserScore,
  });

  const logout = useCallback(() => {
    writeUser(null);
    router.replace("/");
  }, [router, writeUser]);

  useEffect(() => {
    if (!user) {
      router.replace("/");
    }
  }, [user, router]);

  const handleBuy = async (foodId: string) => {
    if (!user) return;
    const success = await buyFood(foodId);
    if (!success) return;
    setCelebrating(true);
    setHighlightFood(foodId);
    setTimeout(() => {
      setCelebrating(false);
      setHighlightFood(null);
    }, 1200);
  };

  if (!user || loading || !summary) {
    return (
      <div className="min-h-screen bg-slate-50">
        <NavBar user={user ?? null} onLogout={logout} />
        <div className="mx-auto max-w-4xl px-4 py-10 text-gray-600">正在加载...</div>
      </div>
    );
  }

  const catPoints = summary.catScore;
  const remaining = nextStageDiff(catPoints);
  const catImage = getCatImage(summary.currentCatStage);

  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar user={user} onLogout={logout} />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl bg-gradient-to-br from-purple-100 to-white p-8 shadow-md">
            <p className="text-sm uppercase text-purple-600">猫咪积分</p>
            <h2 className="mt-2 text-4xl font-bold text-gray-900">{catPoints} 分</h2>
            <p className="mt-1 text-sm text-gray-500">累计喂食价值 · {stageLabel(summary.currentCatStage)}</p>
            <div className="mt-6 flex items-center gap-4">
              <div className={`relative h-48 w-48 overflow-hidden rounded-full border-4 border-purple-200 bg-white ${celebrating ? "animate-pulse" : ""}`}>
                <Image src={catImage} alt="cat" fill sizes="200px" className="object-cover" />
              </div>
              <div>
                {remaining > 0 ? (
                  <p className="text-gray-600">距离下一阶段还差 <span className="font-semibold text-purple-700">{remaining}</span> 分</p>
                ) : (
                  <p className="text-green-600">已经来到了终极猫阶段！</p>
                )}
                <p className="mt-2 text-sm text-gray-500">多做题赚积分，常来商店喂食猫咪即可升级。</p>
              </div>
            </div>
          </div>
          <div className="rounded-3xl bg-white p-8 shadow-md">
            <p className="text-sm uppercase text-gray-400">提示</p>
            <h3 className="mt-2 text-2xl font-semibold text-gray-900">积分使用策略</h3>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-600">
              <li>先用低价食物保持猫咪开心，再把积分攒到下一阶段</li>
              <li>完成高级难度题可一次获得 5 分，迅速冲刺目标</li>
              <li>随时关注当前积分，别忘了三次机会用完后要切换下一题</li>
            </ul>
            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          </div>
        </section>

        <section className="mt-10 rounded-3xl bg-white p-8 shadow-md">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm uppercase text-gray-400">食物商店</p>
              <h3 className="text-2xl font-semibold text-gray-900">挑选食物犒劳你的猫</h3>
              <p className="text-sm text-gray-500">每一件食物都对应一张我们提前生成的 Ark 图片。</p>
            </div>
            <p className="text-sm text-gray-500">可用积分：{summary.totalScore}</p>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {foods.map((food) => (
              <div
                key={food.foodId}
                className={`flex items-center gap-4 rounded-2xl border px-4 py-4 transition ${
                  highlightFood === food.foodId ? "border-green-400 shadow-lg" : "border-gray-100"
                }`}
              >
                <div className="relative h-20 w-20 overflow-hidden rounded-2xl bg-slate-100">
                  <Image src={food.image} alt={food.name} fill sizes="80px" className="object-cover" />
                </div>
                <div className="flex-1">
                  <p className="text-lg font-semibold text-gray-900">{food.name}</p>
                  <p className="text-sm text-gray-500">{food.description}</p>
                  <p className="mt-1 text-purple-700">{food.price} 分</p>
                </div>
                <button
                  onClick={() => handleBuy(food.foodId)}
                  disabled={buyingId === food.foodId}
                  className="rounded-full bg-purple-600 px-4 py-2 text-sm text-white transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {buyingId === food.foodId ? "购买中" : "购买"}
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
