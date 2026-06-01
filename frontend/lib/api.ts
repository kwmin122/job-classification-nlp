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
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseResponse<AnalyzeResponse>(response);
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
