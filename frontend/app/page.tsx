"use client";

import { useState } from "react";
import { CandidateInputPanel } from "@/components/CandidateInputPanel";
import { JobPostingInputPanel } from "@/components/JobPostingInputPanel";
import { RoadmapPreferencePanel } from "@/components/RoadmapPreferencePanel";
import { analyze } from "@/lib/api";
import type { AnalyzeResponse, RoadmapPreferences } from "@/lib/types";

export default function Home() {
  const [jobText, setJobText] = useState("");
  const [candidateText, setCandidateText] = useState("");
  const [preferences, setPreferences] = useState<RoadmapPreferences>({
    duration_weeks: 4,
    difficulty: "입문",
    intensity: "보통",
  });
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    setError(null);
    setIsLoading(true);
    try {
      const response = await analyze({
        job_posting: {
          source_type: "text",
          text: jobText,
        },
        candidate_materials: [
          {
            source_type: "text",
            label: "지원자 자료",
            text: candidateText,
          },
        ],
        roadmap_preferences: preferences,
      });
      setResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="product-topbar">
        <div>
          <p className="eyebrow">JD Fit Roadmap</p>
          <h1>지원 직무에 맞춘 학습 로드맵</h1>
          <p>채용공고와 내 지원 자료를 비교해 부족 역량과 학습 순서를 제안합니다.</p>
        </div>
      </header>

      <div className="dashboard-grid">
        <section className="input-stack" aria-label="분석 입력">
          <JobPostingInputPanel value={jobText} onChange={setJobText} />
          <CandidateInputPanel value={candidateText} onChange={setCandidateText} />
          <RoadmapPreferencePanel value={preferences} onChange={setPreferences} />
          <button className="primary-action" type="button" onClick={handleAnalyze} disabled={isLoading}>
            {isLoading ? "분석 중" : "분석 시작"}
          </button>
          {error ? <p className="error-message">{error}</p> : null}
        </section>

        <section className="workspace" aria-label="분석 결과">
          <header className="workspace-header">
            <div>
              <p className="eyebrow">Analysis Result</p>
              <h2>보완 필요 역량과 로드맵</h2>
            </div>
            <div className="status-chip">{result ? "분석 완료" : "입력 대기"}</div>
          </header>

          {result ? (
            <>
              <section className="summary-grid">
                <div>
                  <span>예측 직무</span>
                  <strong>{result.predicted_job}</strong>
                </div>
                <div>
                  <span>적합도</span>
                  <strong>{result.fit_score.toFixed(0)}점</strong>
                </div>
                <div>
                  <span>부족 역량</span>
                  <strong>{result.missing_skills.length}개</strong>
                </div>
              </section>

              <section className="result-panel">
                <h3>부족 역량</h3>
                {result.missing_skills.map((skill) => (
                  <article key={skill.skill} className="skill-row">
                    <strong>{skill.skill}</strong>
                    <span>
                      {skill.gap_level} / {skill.gap_score.toFixed(0)}점
                    </span>
                    <p>{skill.evidence}</p>
                  </article>
                ))}
              </section>

              <section className="result-panel">
                <h3>추천 자료</h3>
                {result.recommended_resources.map((group) => (
                  <article key={group.skill} className="resource-group">
                    <h4>{group.skill}</h4>
                    {group.recommendations.map((item) => (
                      <a key={item.resource.id} href={item.resource.url} target="_blank" rel="noreferrer">
                        {item.resource.title} · {item.resource.level} · {item.recommend_score.toFixed(0)}점
                      </a>
                    ))}
                  </article>
                ))}
              </section>

              <section className="result-panel">
                <h3>주차별 학습 로드맵</h3>
                {result.weekly_roadmap.map((week) => (
                  <article key={week.week} className="roadmap-week">
                    <strong>
                      {week.week}주차 · {week.goal}
                    </strong>
                    <p>{week.practice}</p>
                  </article>
                ))}
              </section>

              <section className="result-panel">
                <h3>분석 리포트</h3>
                <p>{result.report}</p>
              </section>
            </>
          ) : (
            <p className="empty-state">채용공고와 지원 자료를 입력하면 분석 결과가 여기에 표시됩니다.</p>
          )}
        </section>
      </div>
    </main>
  );
}
