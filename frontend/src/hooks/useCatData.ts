import { useCallback, useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import { StoredUser } from "@/lib/userStorage";

export type FoodItem = {
  foodId: string;
  name: string;
  description: string;
  price: number;
  image: string;
};

export type UserSummary = {
  userId: number;
  totalScore: number;
  catScore: number;
  currentCatStage: number;
  nextStageScore: number;
};

type FoodListResponse = {
  foods: FoodItem[];
};

type BuyResponse = {
  success: boolean;
  newTotalScore: number;
  currentCatStage: number;
};

type Params = {
  user: StoredUser | null;
  onScoreUpdate: (score: number) => void;
};

export function useCatData({ user, onScoreUpdate }: Params) {
  const userId = user?.userId;
  const [foods, setFoods] = useState<FoodItem[]>([]);
  const [summary, setSummary] = useState<UserSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [buyingId, setBuyingId] = useState<string | null>(null);

  const loadFoods = useCallback(async () => {
    const data = await apiGet<FoodListResponse>("/api/foods");
    setFoods(data.foods);
  }, []);

  const loadSummary = useCallback(async () => {
    if (!userId) return;
    const data = await apiGet<UserSummary>(`/api/users/${userId}/summary`);
    setSummary(data);
    onScoreUpdate(data.totalScore);
  }, [onScoreUpdate, userId]);

  const refresh = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      await Promise.all([loadFoods(), loadSummary()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载数据失败");
    } finally {
      setLoading(false);
    }
  }, [loadFoods, loadSummary, userId]);

  useEffect(() => {
    if (userId) {
      refresh();
    } else {
      setFoods([]);
      setSummary(null);
    }
  }, [refresh, userId]);

  const buyFood = useCallback(
    async (foodId: string) => {
      if (!userId) return false;
      setBuyingId(foodId);
      setError(null);
      try {
        const payload = await apiPost<BuyResponse>("/api/buy_food", {
          userId,
          foodId,
        });
        await loadSummary();
        onScoreUpdate(payload.newTotalScore);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "购买失败，稍后重试");
        return false;
      } finally {
        setBuyingId(null);
      }
    },
    [loadSummary, onScoreUpdate, userId],
  );

  return {
    foods,
    summary,
    error,
    loading,
    buyingId,
    buyFood,
    refresh,
  };
}

export default useCatData;
