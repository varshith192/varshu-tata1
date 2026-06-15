const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export async function apiFetch(
  path: string,
  timeoutMs = 4000,
  options?: RequestInit
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
    });
    return res;
  } finally {
    clearTimeout(timer);
  }
}
