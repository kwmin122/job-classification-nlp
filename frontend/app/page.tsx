"use client";

import { useMemo, useState } from "react";
import { CandidateInputPanel } from "@/components/CandidateInputPanel";
import { JobPostingInputPanel } from "@/components/JobPostingInputPanel";
import { RoadmapPreferencePanel } from "@/components/RoadmapPreferencePanel";
import { analyze } from "@/lib/api";
import type { AnalyzeResponse, RoadmapPreferences, SkillGap } from "@/lib/types";

const analysisSteps = ["텍스트 정리", "역량 비교", "자료 검색", "로드맵 생성"];

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

  const topGap = useMemo(() => {
    if (!result?.missing_skills.length) return null;
    return [...result.missing_skills].sort((a, b) => b.gap_score - a.gap_score)[0];
  }, [result]);

  const canAnalyze = jobText.trim().length >= 20 && candidateText.trim().length >= 20 && !isLoading;

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
      setError(toUserError(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="analysis-rail" aria-label="분석 입력">
        <div className="rail-brand">
          <span className="brand-mark">JD</span>
          <div>
            <p>Fit Roadmap</p>
            <strong>지원 전 역량 점검</strong>
          </div>
        </div>

        <div className="rail-intro">
          <p className="eyebrow">Readiness Workbench</p>
          <h1>채용공고 기준으로 내 자료의 빈칸을 찾습니다.</h1>
          <p>공고 요구사항과 내 경험 문장을 비교하고, 부족 역량별 학습 자료와 주차별 실행 계획을 만듭니다.</p>
        </div>

        <div className="input-sequence" aria-label="분석 단계">
          {analysisSteps.map((step, index) => (
            <span key={step} className={isLoading ? "active" : ""}>
              {index + 1}. {step}
            </span>
          ))}
        </div>

        <JobPostingInputPanel value={jobText} onChange={setJobText} />
        <CandidateInputPanel value={candidateText} onChange={setCandidateText} />
        <RoadmapPreferencePanel value={preferences} onChange={setPreferences} />

        <button className="primary-action" type="button" onClick={handleAnalyze} disabled={!canAnalyze}>
          {isLoading ? "분석 중입니다" : "분석 시작"}
        </button>
        <p className="rail-note">각 입력은 최소 20자 이상이어야 합니다. 파일과 URL 추출은 다음 구현 단계입니다.</p>
        {error ? <p className="error-message">{error}</p> : null}
      </aside>

      <section className="result-workbench" aria-label="분석 결과">
        <header className="workbench-header">
          <div>
            <p className="eyebrow">Career Evidence Analysis</p>
            <h2>보완 필요 역량과 학습 경로</h2>
            <p>분석 결과는 지원 판단을 대신하지 않고, 지원 자료에서 보강할 근거와 학습 순서를 정리합니다.</p>
          </div>
          <div className="method-stack" aria-label="분석 방식">
            <span>{result?.retrieval_mode ?? "대기 중"}</span>
            <span>{result?.embedding_model ?? "resource DB"}</span>
          </div>
        </header>

        {isLoading ? <LoadingState /> : null}
        {!isLoading && !result ? <EmptyState /> : null}
        {!isLoading && result ? <AnalysisResult result={result} topGap={topGap} /> : null}
      </section>
    </main>
  );
}

function AnalysisResult({ result, topGap }: { result: AnalyzeResponse; topGap: SkillGap | null }) {
  return (
    <div className="result-stack">
      <section className="score-board" aria-label="요약 점수">
        <Metric label="예측 직무" value={result.predicted_job} />
        <Metric label="적합도" value={`${result.fit_score.toFixed(0)}점`} tone={scoreTone(result.fit_score)} />
        <Metric label="부족 역량" value={`${result.missing_skills.length}개`} />
        <Metric label="우선 보완" value={topGap?.skill ?? "없음"} />
      </section>

      <section className="insight-layout">
        <article className="priority-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Top Priority</p>
              <h3>{topGap ? `${topGap.skill} 보완이 먼저입니다` : "뚜렷한 부족 역량이 없습니다"}</h3>
            </div>
            {topGap ? <span className={gapTone(topGap.gap_score)}>{topGap.gap_level}</span> : null}
          </div>
          {topGap ? (
            <>
              <div className="priority-score">
                <span style={{ width: `${topGap.gap_score}%` }} />
              </div>
              <p>{topGap.evidence}</p>
            </>
          ) : (
            <p>현재 입력에서는 공고 요구 역량과 지원자 자료 사이의 큰 격차가 잡히지 않았습니다.</p>
          )}
        </article>

        <article className="report-card">
          <p className="eyebrow">Report</p>
          <p>{result.report}</p>
        </article>
      </section>

      <section className="evidence-grid" aria-label="근거 분석">
        <EvidenceColumn title="공고 요구 역량" items={result.required_skills.map((item) => item.skill)} />
        <EvidenceColumn title="내 자료에서 확인된 역량" items={result.owned_skills.map((item) => item.skill)} />
        <EvidenceColumn title="보완 필요 역량" items={result.missing_skills.map((item) => item.skill)} />
      </section>

      <section className="gap-table" aria-label="부족 역량 상세">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Gap Matrix</p>
            <h3>부족 정도와 판단 근거</h3>
          </div>
          <span className="quiet-pill">높은 점수 우선</span>
        </div>
        <div className="gap-list">
          {result.missing_skills.map((skill) => (
            <article key={skill.skill} className="gap-row">
              <div>
                <strong>{skill.skill}</strong>
                <p>{skill.evidence}</p>
              </div>
              <div className="gap-score-cell">
                <span className={gapTone(skill.gap_score)}>{skill.gap_level}</span>
                <b>{skill.gap_score.toFixed(0)}</b>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="roadmap-board" aria-label="주차별 학습 로드맵">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Weekly Roadmap</p>
            <h3>{result.roadmap_preferences.duration_weeks}주 학습 계획</h3>
          </div>
          <span className="quiet-pill">
            {result.roadmap_preferences.difficulty} · {result.roadmap_preferences.intensity}
          </span>
        </div>
        <div className="week-grid">
          {result.weekly_roadmap.map((week) => (
            <article key={week.week} className="week-card">
              <span>{week.week}주차</span>
              <strong>{week.goal}</strong>
              <p>{week.practice}</p>
              {week.recommended_titles.length ? (
                <ul>
                  {week.recommended_titles.map((title) => (
                    <li key={title}>{title}</li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <section className="resource-board" aria-label="추천 자료">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Curated RAG Resources</p>
            <h3>부족 역량별 추천 자료</h3>
          </div>
          <span className="quiet-pill">DB 기반 검색</span>
        </div>
        <div className="resource-columns">
          {result.recommended_resources.map((group) => (
            <article key={group.skill} className="resource-column">
              <h4>{group.skill}</h4>
              {group.recommendations.map((item) => (
                <a key={item.resource.id} href={item.resource.url} target="_blank" rel="noreferrer">
                  <span>{item.resource.type}</span>
                  <strong>{item.resource.title}</strong>
                  <small>
                    {item.resource.level} · 신뢰도 {item.resource.reliability}/5 · {item.recommend_score.toFixed(0)}점
                  </small>
                </a>
              ))}
            </article>
          ))}
        </div>
      </section>

      <section className="method-card" aria-label="방법 공개">
        <p>{result.rag_scope_note}</p>
        <code>{result.scoring_formula}</code>
        <span>chunking: {result.chunking_strategy}</span>
      </section>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className={`metric-card ${tone ?? ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EvidenceColumn({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="evidence-column">
      <h3>{title}</h3>
      {items.length ? (
        <div>
          {items.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      ) : (
        <p>확인된 항목 없음</p>
      )}
    </article>
  );
}

function EmptyState() {
  return (
    <section className="empty-state">
      <div>
        <p className="eyebrow">Ready</p>
        <h3>채용공고와 내 자료를 넣으면 분석 보드가 생성됩니다.</h3>
        <p>결과에는 직무 적합도, 부족 역량, 추천 자료, 주차별 로드맵, 분석 리포트가 포함됩니다.</p>
      </div>
      <ol>
        <li>채용공고의 자격요건을 붙여넣기</li>
        <li>자소서나 포트폴리오 근거 붙여넣기</li>
        <li>목표 기간과 현재 수준 선택</li>
      </ol>
    </section>
  );
}

function LoadingState() {
  return (
    <section className="loading-state" aria-live="polite">
      <div>
        <p className="eyebrow">Analyzing</p>
        <h3>요구 역량과 지원자 근거를 비교하고 있습니다.</h3>
      </div>
      <div className="loading-bars">
        <span />
        <span />
        <span />
      </div>
    </section>
  );
}

function scoreTone(score: number) {
  if (score >= 75) return "tone-good";
  if (score >= 45) return "tone-warn";
  return "tone-risk";
}

function gapTone(score: number) {
  if (score >= 70) return "state-pill risk";
  if (score >= 40) return "state-pill warn";
  return "state-pill good";
}

function toUserError(error: unknown) {
  const message = error instanceof Error ? error.message : "분석 중 오류가 발생했습니다.";
  if (message.includes("candidate text is too short")) {
    return "지원자 자료가 너무 짧습니다. 프로젝트 경험이나 기술 사용 근거를 20자 이상 입력해 주세요.";
  }
  if (message.includes("job_posting text is too short")) {
    return "채용공고 내용이 너무 짧습니다. 자격요건이나 우대사항을 20자 이상 입력해 주세요.";
  }
  return message;
}
