"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { GapMatrix } from "@/components/GapMatrix";
import { JsonInputPanel } from "@/components/JsonInputPanel";
import { ReportPanel } from "@/components/ReportPanel";
import { ResourceRecommendations } from "@/components/ResourceRecommendations";
import { RoadmapPanel } from "@/components/RoadmapPanel";
import { SummaryStrip } from "@/components/SummaryStrip";
import { fetchSample, recommend } from "@/lib/api";
import type { COutput, RecommendResponse } from "@/lib/types";

const fallbackSample: COutput = {
  predicted_job: "백엔드 개발자",
  fit_score: 72,
  matched_skills: ["Java", "Spring Boot", "MySQL", "REST API"],
  skill_gaps: [
    {
      skill: "Docker",
      gap_score: 82,
      gap_level: "높음",
      importance: "필수",
      evidence: "JD에는 Docker 기반 배포 경험이 요구되지만 지원자 텍스트에는 컨테이너 기반 배포 경험이 나타나지 않음"
    },
    {
      skill: "AWS",
      gap_score: 64,
      gap_level: "중간",
      importance: "우대",
      evidence: "클라우드 운영 또는 EC2 배포 경험이 구체적으로 드러나지 않음"
    },
    {
      skill: "CI/CD",
      gap_score: 76,
      gap_level: "높음",
      importance: "필수",
      evidence: "GitHub Actions 또는 배포 자동화 경험이 지원자 텍스트에 확인되지 않음"
    }
  ]
};

export default function Home() {
  const [jsonInput, setJsonInput] = useState(JSON.stringify(fallbackSample, null, 2));
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const autoRan = useRef(false);

  const sortedSkillRecommendations = useMemo(
    () => result?.skill_recommendations ?? [],
    [result]
  );

  async function handleLoadSample() {
    setError(null);
    try {
      const sample = await fetchSample();
      setJsonInput(JSON.stringify(sample, null, 2));
    } catch {
      setJsonInput(JSON.stringify(fallbackSample, null, 2));
      setError("백엔드 샘플 호출에 실패해서 내장 샘플을 불러왔습니다.");
    }
  }

  async function handleAnalyze() {
    setError(null);
    setIsLoading(true);
    try {
      const parsed = JSON.parse(jsonInput) as COutput;
      const response = await recommend(parsed);
      setResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (autoRan.current || typeof window === "undefined") {
      return;
    }
    if (new URLSearchParams(window.location.search).get("auto") === "1") {
      autoRan.current = true;
      void handleAnalyze();
    }
  }, []);

  return (
    <main className="dashboard-shell">
      <header className="product-topbar">
        <div>
          <p className="eyebrow">JD Fit Roadmap</p>
          <h1>지원 직무에 맞춘 학습 로드맵</h1>
          <p>
            채용공고와 지원자 자료의 격차를 바탕으로 먼저 보완할 역량과 검증 가능한 학습 자료를 제안합니다.
          </p>
        </div>
        <div className="topbar-actions" aria-label="분석 방식 요약">
          <span className="method-chip">80개 큐레이션 자료 DB</span>
          <span className="method-chip">부족 역량 기반 추천</span>
        </div>
      </header>

      <div className="dashboard-grid">
        <JsonInputPanel
          value={jsonInput}
          onChange={setJsonInput}
          onLoadSample={handleLoadSample}
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          error={error}
        />
        <section className="workspace" aria-label="추천 결과">
          <header className="workspace-header">
            <div>
              <p className="eyebrow">분석 결과</p>
              <h2>개인 맞춤 보완 계획</h2>
              <p>
                부족 역량의 우선순위, 추천 자료, 실행 로드맵, 리포트를 한 화면에서 확인합니다.
              </p>
            </div>
            <div className="status-chip">{result ? "로드맵 생성 완료" : "분석 자료 대기"}</div>
          </header>
          <SummaryStrip result={result} />
          <GapMatrix items={sortedSkillRecommendations} />
          <ResourceRecommendations items={sortedSkillRecommendations} />
          <RoadmapPanel items={result?.roadmap ?? []} />
          <ReportPanel
            report={result?.report ?? null}
            formula={result?.scoring_formula ?? null}
            ragScope={result?.rag_scope_note ?? null}
            retrievalMode={result?.retrieval_mode ?? null}
            embeddingModel={result?.embedding_model ?? null}
            chunkingStrategy={result?.chunking_strategy ?? null}
          />
        </section>
      </div>
    </main>
  );
}
