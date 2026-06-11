import type { AnalyzeRequest, AnalyzeResponse, ExtractedText } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    let detail: string | undefined;
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      detail = parsed.detail;
    } catch {
      detail = undefined;
    }
    throw new Error(detail || body || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function analyze(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  // 분석 서버가 다운/지연이면 무한 대기 대신 명확히 실패시킨다(가짜 100%→되돌아감 방지).
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 120_000);
  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    return await parseResponse<AnalyzeResponse>(response);
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("분석 서버 응답이 지연됩니다. 서버가 실행 중인지 확인하고 잠시 후 다시 시도해 주세요.");
    }
    if (e instanceof TypeError) {
      throw new Error("분석 서버에 연결하지 못했어요. 백엔드(8010)가 실행 중인지 확인해 주세요.");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function extractJobPostingFromUrl(url: string): Promise<ExtractedText> {
  const response = await fetch(`${API_BASE}/extract/job-posting`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      source_type: "url",
      url
    })
  });
  return parseResponse<ExtractedText>(response);
}

export async function extractJobPostingFromFile(file: File): Promise<ExtractedText> {
  const formData = new FormData();
  formData.append("source_type", "file");
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/extract/job-posting`, {
    method: "POST",
    body: formData
  });
  return parseResponse<ExtractedText>(response);
}

export async function extractCandidateMaterialFromFile(file: File, label: string): Promise<ExtractedText> {
  const formData = new FormData();
  formData.append("source_type", "file");
  formData.append("label", label);
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/extract/candidate-material`, {
    method: "POST",
    body: formData
  });
  return parseResponse<ExtractedText>(response);
}
