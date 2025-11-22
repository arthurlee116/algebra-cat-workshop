import { useEffect, useRef, useState } from "react";

import { StoredUser } from "@/lib/userStorage";

export type ScoreAnimation = "up" | "down" | null;

export function useScoreAnimation(user: StoredUser | null): ScoreAnimation {
  const [animation, setAnimation] = useState<ScoreAnimation>(null);
  const previousScore = useRef<number | null>(null);

  useEffect(() => {
    if (!user) {
      previousScore.current = null;
      setAnimation(null);
      return;
    }

    const currentScore = user.total_score;
    const lastScore = previousScore.current;
    previousScore.current = currentScore;

    if (lastScore === null || currentScore === lastScore) {
      return;
    }

    setAnimation(currentScore > lastScore ? "up" : "down");
    const timer = setTimeout(() => setAnimation(null), 2000);
    return () => clearTimeout(timer);
  }, [user]);

  return animation;
}

export default useScoreAnimation;
