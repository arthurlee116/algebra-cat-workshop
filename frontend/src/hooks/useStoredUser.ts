"use client";

import { useCallback, useState } from "react";
import {
  StoredUser,
  clearStoredUser,
  loadStoredUser,
  persistStoredUser,
} from "@/lib/userStorage";

export function useStoredUser() {
  const [user, setUser] = useState<StoredUser | null>(() => loadStoredUser());

  const writeUser = useCallback((value: StoredUser | null) => {
    if (value) {
      persistStoredUser(value);
    } else {
      clearStoredUser();
    }
    setUser(value);
  }, []);

  const updateUserScore = useCallback((score: number) => {
    setUser((prev) => {
      if (!prev) {
        return prev;
      }
      const next = { ...prev, total_score: score };
      persistStoredUser(next);
      return next;
    });
  }, []);

  return { user, writeUser, updateUserScore };
}
