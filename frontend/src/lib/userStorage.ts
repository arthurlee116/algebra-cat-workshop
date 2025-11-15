export type StoredUser = {
  userId: number;
  chinese_name: string;
  english_name: string;
  class_name: string;
  total_score: number;
};

const STORAGE_KEY = "math-cat-user";

export function loadStoredUser(): StoredUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredUser) : null;
  } catch (error) {
    console.error("Failed to parse stored user", error);
    return null;
  }
}

export function persistStoredUser(user: StoredUser): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(STORAGE_KEY);
}
