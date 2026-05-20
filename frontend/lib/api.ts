import type { COutput, RecommendResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchSample(): Promise<COutput> {
  const response = await fetch(`${API_BASE}/sample`, { cache: "no-store" });
  return parseResponse<COutput>(response);
}

export async function recommend(payload: COutput): Promise<RecommendResponse> {
  const response = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseResponse<RecommendResponse>(response);
}

