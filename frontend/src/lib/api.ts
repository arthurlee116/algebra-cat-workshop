const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "服务器返回错误";
    try {
      const payload = await response.json();
      message = payload.detail ?? JSON.stringify(payload);
    } catch {
      message = response.statusText;
    }
    throw new Error(message);
  }
  return response.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, {
    method: "GET",
  });
}

export { API_BASE };
