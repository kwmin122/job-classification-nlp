"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AnalysisSettingsPanel } from "@/components/AnalysisSettingsPanel";
import { CandidateInputPanel } from "@/components/CandidateInputPanel";
import { JobPostingInputPanel } from "@/components/JobPostingInputPanel";
import { RoadmapPreferencePanel } from "@/components/RoadmapPreferencePanel";
import {
  analyze,
  extractCandidateMaterialFromFile,
  extractJobPostingFromUrl,
} from "@/lib/api";
import type {
  AnalyzeResponse,
  CandidateMaterialDraft,
  JobInputMode,
  RoadmapPreferences,
  SkillRecommendation,
} from "@/lib/types";

/* ─── constants ─────────────────────────────────────────────────── */
const ANALYSIS_STEPS = ["입력 확인", "역량 비교", "자료 매칭", "로드맵 출력"];

/* ─── AnimatedNumber ────────────────────────────────────────────── */
function AnimatedNumber({ value }: { value: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const rounded = Math.round(value);
    el.textContent = "0";
    if (rounded === 0) return;
    let frame = 0;
    const totalFrames = Math.round(1000 / 16);
    const timer = setInterval(() => {
      frame++;
      el.textContent = String(Math.round((frame / totalFrames) * rounded));
      if (frame >= totalFrames) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [value]);
  return <span ref={ref}>{Math.round(value)}</span>;
}

const createCandidate = (id: string): CandidateMaterialDraft => ({
  id,
  label: "자소서",
  sourceMode: "file",
  text: "",
  warnings: [],
  error: null,
  isExtracting: false,
});

/* ─── icons (inline SVG) ────────────────────────────────────────── */
function IconHome() {
  return (
    <svg className="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 9.5L10 3l7 6.5V17a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" />
      <path d="M8 18v-6h4v6" />
    </svg>
  );
}
function IconGap() {
  return (
    <svg className="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="3" y="12" width="3" height="6" rx="1" />
      <rect x="8.5" y="7" width="3" height="11" rx="1" />
      <rect x="14" y="3" width="3" height="15" rx="1" />
      <path d="M4.5 10l4-4 3.5 3 4-5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function IconRoadmap() {
  return (
    <svg className="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="3" y="4" width="14" height="13" rx="2" />
      <path d="M3 8h14M7 4v4M13 4v4" strokeLinecap="round" />
    </svg>
  );
}
function IconBook() {
  return (
    <svg className="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 3h10a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M7 7h6M7 10h6M7 13h4" strokeLinecap="round" />
    </svg>
  );
}
function IconBack() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M10 3L5 8l5 5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ─── Sidebar ───────────────────────────────────────────────────── */
type SidebarItem = {
  label: string;
  icon: React.ReactNode;
  anchor?: string;
  action?: () => void;
  disabled?: boolean;
};

function Sidebar({
  hasDashboard,
  onNewAnalysis,
}: {
  hasDashboard: boolean;
  onNewAnalysis: () => void;
}) {
  function scrollTo(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const items: SidebarItem[] = [
    { label: "새 분석", icon: <IconHome />, action: onNewAnalysis },
    {
      label: "역량 격차",
      icon: <IconGap />,
      disabled: !hasDashboard,
      action: () => scrollTo("gap-section"),
    },
    {
      label: "학습 로드맵",
      icon: <IconRoadmap />,
      disabled: !hasDashboard,
      action: () => scrollTo("roadmap-section"),
    },
    {
      label: "추천 자료",
      icon: <IconBook />,
      disabled: !hasDashboard,
      action: () => scrollTo("resources-section"),
    },
  ];

  return (
    <nav className="sidebar" aria-label="주요 메뉴">
      <div className="sidebar-logo">
        <span className="brand-mark">JD</span>
        <div className="sidebar-logo-text">
          <strong>Fit Dashboard</strong>
          <span>역량 격차 분석</span>
        </div>
      </div>
      <ul className="sidebar-nav">
        {items.map((item) => (
          <li key={item.label}>
            <button
              type="button"
              className={item.disabled ? "disabled-nav" : ""}
              onClick={item.action}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/* ─── Root Page ─────────────────────────────────────────────────── */
export default function Home() {
  const [jobText, setJobText] = useState("");
  const [jobSourceMode, setJobSourceMode] = useState<JobInputMode>("url");
  const [jobUrl, setJobUrl] = useState("");
  const [jobSourceName, setJobSourceName] = useState<string | undefined>();
  const [jobExtractor, setJobExtractor] = useState<string | undefined>();
  const [jobWarnings, setJobWarnings] = useState<string[]>([]);
  const [jobExtractionError, setJobExtractionError] = useState<string | null>(null);
  const [isJobExtracting, setIsJobExtracting] = useState(false);
  const [candidateMaterials, setCandidateMaterials] = useState<CandidateMaterialDraft[]>([
    createCandidate("candidate-1"),
  ]);
  const [openaiApiKey, setOpenaiApiKey] = useState("");
  const [preferences, setPreferences] = useState<RoadmapPreferences>({
    duration_weeks: 4,
    difficulty: "입문",
    intensity: "보통",
  });
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const candidateMaterialsForAnalysis = candidateMaterials.filter(
    (m) => m.text.trim().length >= 20,
  );
  const candidateTextLength = candidateMaterials.reduce(
    (sum, m) => sum + m.text.trim().length,
    0,
  );
  const canAnalyze = jobText.trim().length >= 20 && candidateTextLength >= 20 && !isLoading;

  async function handleExtractJobUrl() {
    setJobExtractionError(null);
    setIsJobExtracting(true);
    try {
      const extracted = await extractJobPostingFromUrl(jobUrl.trim());
      setJobText(extracted.text);
      setJobSourceName(extracted.source_name ?? jobUrl.trim());
      setJobExtractor(extracted.extractor);
      setJobWarnings(extracted.warnings);
    } catch (e) {
      setJobExtractionError(toUserError(e));
    } finally {
      setIsJobExtracting(false);
    }
  }

  function handleCandidateChange(id: string, patch: Partial<CandidateMaterialDraft>) {
    setCandidateMaterials((cur) =>
      cur.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    );
  }

  async function handleExtractCandidateFile(id: string, file: File) {
    const label = candidateMaterials.find((m) => m.id === id)?.label ?? "지원자 자료";
    handleCandidateChange(id, { error: null, isExtracting: true });
    try {
      const extracted = await extractCandidateMaterialFromFile(file, label);
      handleCandidateChange(id, {
        text: extracted.text,
        sourceName: extracted.source_name ?? file.name,
        extractor: extracted.extractor,
        warnings: extracted.warnings,
        error: null,
        isExtracting: false,
      });
    } catch (e) {
      handleCandidateChange(id, { error: toUserError(e), isExtracting: false });
    }
  }

  async function handleAnalyze() {
    setError(null);
    setIsLoading(true);
    try {
      const response = await analyze({
        job_posting: { source_type: "text", text: jobText },
        candidate_materials: candidateMaterialsForAnalysis.map((m) => ({
          source_type: "text" as const,
          label: m.label || "지원자 자료",
          text: m.text,
        })),
        roadmap_preferences: preferences,
        openai_api_key: openaiApiKey.trim() || undefined,
      });
      setResult(response);
    } catch (e) {
      setError(toUserError(e));
    } finally {
      setIsLoading(false);
    }
  }

  function handleReset() {
    setResult(null);
    setError(null);
  }

  return (
    <div className="app-shell">
      <Sidebar hasDashboard={!!result} onNewAnalysis={handleReset} />
      <div className="main-panel">
        {result ? (
          <DashboardPage result={result} onReset={handleReset} />
        ) : (
          <SetupPage
            jobText={jobText}
            setJobText={setJobText}
            jobSourceMode={jobSourceMode}
            setJobSourceMode={setJobSourceMode}
            jobUrl={jobUrl}
            setJobUrl={setJobUrl}
            onExtractJobUrl={handleExtractJobUrl}
            isJobExtracting={isJobExtracting}
            jobSourceName={jobSourceName}
            jobExtractor={jobExtractor}
            jobWarnings={jobWarnings}
            jobExtractionError={jobExtractionError}
            candidateMaterials={candidateMaterials}
            onMaterialChange={handleCandidateChange}
            onAddMaterial={() =>
              setCandidateMaterials((cur) => [
                ...cur,
                createCandidate(`candidate-${Date.now()}`),
              ])
            }
            onRemoveMaterial={(id) =>
              setCandidateMaterials((cur) => cur.filter((m) => m.id !== id))
            }
            onExtractCandidateFile={handleExtractCandidateFile}
            openaiApiKey={openaiApiKey}
            setOpenaiApiKey={setOpenaiApiKey}
            preferences={preferences}
            setPreferences={setPreferences}
            onAnalyze={handleAnalyze}
            canAnalyze={canAnalyze}
            isLoading={isLoading}
            error={error}
          />
        )}
      </div>
    </div>
  );
}

/* ─── Setup Page ────────────────────────────────────────────────── */
function SetupPage({
  jobText,
  setJobText,
  jobSourceMode,
  setJobSourceMode,
  jobUrl,
  setJobUrl,
  onExtractJobUrl,
  isJobExtracting,
  jobSourceName,
  jobExtractor,
  jobWarnings,
  jobExtractionError,
  candidateMaterials,
  onMaterialChange,
  onAddMaterial,
  onRemoveMaterial,
  onExtractCandidateFile,
  openaiApiKey,
  setOpenaiApiKey,
  preferences,
  setPreferences,
  onAnalyze,
  canAnalyze,
  isLoading,
  error,
}: {
  jobText: string;
  setJobText: (v: string) => void;
  jobSourceMode: JobInputMode;
  setJobSourceMode: (v: JobInputMode) => void;
  jobUrl: string;
  setJobUrl: (v: string) => void;
  onExtractJobUrl: () => void;
  isJobExtracting: boolean;
  jobSourceName?: string;
  jobExtractor?: string;
  jobWarnings: string[];
  jobExtractionError: string | null;
  candidateMaterials: CandidateMaterialDraft[];
  onMaterialChange: (id: string, patch: Partial<CandidateMaterialDraft>) => void;
  onAddMaterial: () => void;
  onRemoveMaterial: (id: string) => void;
  onExtractCandidateFile: (id: string, f: File) => void;
  openaiApiKey: string;
  setOpenaiApiKey: (v: string) => void;
  preferences: RoadmapPreferences;
  setPreferences: (v: RoadmapPreferences) => void;
  onAnalyze: () => void;
  canAnalyze: boolean;
  isLoading: boolean;
  error: string | null;
}) {
  return (
    <div className="setup-page">
      {/* Header */}
      <header className="setup-header">
        <div>
          <p className="eyebrow">Career Readiness Dashboard</p>
          <h1>채용공고 기준 역량 점검</h1>
          <p>지원하려는 채용공고와 내 자료를 비교해 부족 역량과 주차별 학습 로드맵을 확인합니다.</p>
        </div>
        <div className="step-pills" aria-label="분석 단계">
          {ANALYSIS_STEPS.map((step, i) => (
            <span key={step} className={isLoading ? "active" : ""}>
              {i + 1}. {step}
            </span>
          ))}
        </div>
      </header>

      {/* Input grid */}
      <div className="input-grid">
        <JobPostingInputPanel
          value={jobText}
          onChange={setJobText}
          sourceMode={jobSourceMode}
          onSourceModeChange={setJobSourceMode}
          url={jobUrl}
          onUrlChange={setJobUrl}
          onExtractUrl={onExtractJobUrl}
          isExtracting={isJobExtracting}
          sourceName={jobSourceName}
          extractor={jobExtractor}
          warnings={jobWarnings}
          error={jobExtractionError}
        />
        <div className="input-right-col">
          <CandidateInputPanel
            materials={candidateMaterials}
            onMaterialChange={onMaterialChange}
            onAddMaterial={onAddMaterial}
            onRemoveMaterial={onRemoveMaterial}
            onFileChange={onExtractCandidateFile}
          />
          <div className="settings-row">
            <AnalysisSettingsPanel
              openaiApiKey={openaiApiKey}
              onOpenaiApiKeyChange={setOpenaiApiKey}
            />
            <RoadmapPreferencePanel value={preferences} onChange={setPreferences} />
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="cta-bar">
        <div className="cta-inner">
          <button
            className="primary-action"
            type="button"
            onClick={onAnalyze}
            disabled={!canAnalyze}
          >
            {isLoading ? "분석 중입니다" : "분석 시작"}
          </button>
          <p className="cta-note">URL/PDF/TXT는 먼저 텍스트로 추출되며, 수정 가능한 미리보기를 기준으로 분석합니다.</p>
        </div>
        {error ? <p className="error-message">{error}</p> : null}
        {isLoading ? (
          <div className="loading-strip" role="status" aria-live="polite">
            <div className="loading-dots">
              <span /><span /><span />
            </div>
            <p>공고 요건과 지원자 근거를 비교하고 있습니다 — 잠시만 기다려 주세요.</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/* ─── Dashboard Page ────────────────────────────────────────────── */
function DashboardPage({
  result,
  onReset,
}: {
  result: AnalyzeResponse;
  onReset: () => void;
}) {
  const topTarget = useMemo(() => result.recommended_resources[0] ?? null, [result]);

  const gapRows = [
    ...result.missing_skills.map((s) => ({ ...s, target_type: "gap" as const })),
    ...result.partial_skills.map((s) => ({ ...s, target_type: "partial" as const })),
  ];

  const roundedScore = Math.round(result.fit_score);

  const gapChartData = gapRows
    .slice(0, 8)
    .map((s) => ({ name: s.skill, value: s.gap_score, type: s.target_type }));

  return (
    <div className="dashboard-page">
      {/* Top bar */}
      <div className="dash-topbar">
        <div className="dash-topbar-left">
          <p className="eyebrow">분석 결과</p>
          <h1>
            {result.predicted_job} 직무 · 적합도{" "}
            <AnimatedNumber value={result.fit_score} />점
          </h1>
          <p>
            부족 역량 {result.missing_skills.length}개 · 보완 필요{" "}
            {result.partial_skills.length}개 · 추천 자료{" "}
            {result.recommended_resources.reduce(
              (s, r) => s + r.recommendations.length,
              0,
            )}
            개
          </p>
        </div>
        <div className="dash-topbar-right">
          <button className="back-btn" type="button" onClick={onReset}>
            <IconBack /> 다시 분석
          </button>
        </div>
      </div>

      {/* jd_quality 경고 배너 */}
      {result.jd_quality === "weak" && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-800 text-sm mb-4">
          ⚠️ 이 공고에서 명확한 기술 요구를 찾지 못했습니다. 개발 직무 공고인지 확인하거나 본문을 직접 붙여넣어 주세요.
        </div>
      )}

      {/* Dashboard content */}
      <div className={result.jd_quality === "weak" ? "dash-content opacity-40 pointer-events-none select-none" : "dash-content"}>
        {/* KPI Row */}
        <section className="score-board reveal-1" aria-label="요약 점수">
          <div className={`metric-card ${scoreTone(roundedScore)}`}>
            <span>예측 직무</span>
            <strong>{result.predicted_job}</strong>
          </div>
          <div className={`metric-card ${scoreTone(roundedScore)}`}>
            <span>적합도</span>
            <strong><AnimatedNumber value={result.fit_score} />점</strong>
          </div>
          <div className="metric-card tone-risk">
            <span>부족 역량</span>
            <strong>{result.missing_skills.length}개</strong>
          </div>
          <div className="metric-card tone-warn">
            <span>보완 필요</span>
            <strong>{result.partial_skills.length}개</strong>
          </div>
        </section>

        {/* Insight row: gauge + gap chart */}
        <div className="insight-row reveal-2">
          {/* Fit Gauge */}
          <div className="widget-card">
            <div>
              <p className="eyebrow">Fit Score</p>
              <h3>직무 적합도</h3>
            </div>
            <div className="fit-gauge-wrap">
              <FitGauge score={result.fit_score} />
              <div className="fit-gauge-meta">
                <strong><AnimatedNumber value={result.fit_score} /></strong>
                <span>/ 100점</span>
                <div className="fit-gauge-chips">
                  <span className={`state-pill ${scoreTone(roundedScore)}`}>
                    {roundedScore >= 75
                      ? "지원 적합"
                      : roundedScore >= 45
                        ? "보완 후 지원"
                        : "추가 준비 필요"}
                  </span>
                </div>
              </div>
            </div>
            {topTarget ? (
              <div>
                <p className="eyebrow">Top Priority</p>
                <p style={{ margin: "4px 0 0", fontSize: ".86rem", color: "var(--ink-soft)" }}>
                  <strong>{topTarget.skill}</strong> — {topTarget.evidence}
                </p>
              </div>
            ) : null}
          </div>

          {/* Gap Chart */}
          <div className="widget-card">
            <div>
              <p className="eyebrow">Skill Gap Analysis</p>
              <h3>역량 격차 점수</h3>
            </div>
            {gapChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={Math.max(gapChartData.length * 34 + 16, 120)}>
                <BarChart
                  data={gapChartData}
                  layout="vertical"
                  margin={{ left: 0, right: 40, top: 4, bottom: 4 }}
                >
                  <XAxis type="number" domain={[0, 100]} hide />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={92}
                    tick={{ fontSize: 12, fill: "#485e44" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip formatter={(v) => [`${v}점`, "격차"]} cursor={{ fill: "rgba(200,229,90,.15)" }} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} background={{ fill: "#eef4eb", radius: 6 }}>
                    {gapChartData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={entry.type === "gap" ? "#f5c0b8" : "#f9d99a"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ color: "var(--muted)", fontSize: ".84rem" }}>부족 역량이 없습니다.</p>
            )}
          </div>
        </div>

        {/* Skills overview */}
        <div className="evidence-section reveal-3" id="gap-section">
          <div className="evidence-section-title">
            <h3>역량 분류 현황</h3>
            <span className="quiet-pill">공고 기준</span>
          </div>
          <div className="evidence-grid" aria-label="근거 분석">
            <EvidenceColumn title="공고 요구 역량" items={result.required_skills.map((s) => s.skill)} />
            <EvidenceColumn title="보유 역량" items={result.owned_skills.map((s) => s.skill)} />
            <EvidenceColumn title="보완 필요" items={result.partial_skills.map((s) => s.skill)} />
            <EvidenceColumn title="부족 역량" items={result.missing_skills.map((s) => s.skill)} />
          </div>
        </div>

        {/* 공고 명시 기술 전체 — structured_skills */}
        {result.structured_skills && result.structured_skills.length > 0 && (
          <div className="structured-skills-section">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">공고 명시 기술</p>
                <h3>채용공고 요구 스킬 전체</h3>
              </div>
            </div>
            <div className="skill-tags">
              {result.structured_skills.map((s) => (
                <span key={s} className="skill-tag">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* Gap matrix detail */}
        {gapRows.length > 0 ? (
          <div className="gap-table reveal-4">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Gap Matrix</p>
                <h3>보완 우선순위와 판단 근거</h3>
              </div>
              <span className="quiet-pill">부족 역량 우선</span>
            </div>
            <div className="gap-list">
              {gapRows.map((skill) => (
                <article key={skill.skill} className="gap-row">
                  <div>
                    <strong>
                      {skill.skill}
                      <span className={`target-chip ${skill.target_type}`}>
                        {skill.target_type === "gap" ? "부족" : "보완"}
                      </span>
                      {skill.coverage !== undefined && (
                        <span className={`coverage-tag ${
                          skill.coverage >= 70 ? "cov-owned" :
                          skill.coverage >= 40 ? "cov-partial" :
                          "cov-missing"
                        }`}>
                          충족도 {skill.coverage.toFixed(0)}%
                        </span>
                      )}
                    </strong>
                    <p>{skill.evidence}</p>
                  </div>
                  <div className="gap-score-cell">
                    <span className={gapTone(skill.gap_score)}>{skill.gap_level}</span>
                    <b>{skill.gap_score.toFixed(0)}</b>
                  </div>
                </article>
              ))}
            </div>
          </div>
        ) : null}

        {/* Weekly Roadmap */}
        <div className="roadmap-board reveal-5" id="roadmap-section">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Weekly Roadmap</p>
              <h3>
                {result.roadmap_preferences.duration_weeks}주 학습 계획
              </h3>
              <p>
                {result.roadmap_preferences.difficulty} 수준 ·{" "}
                {result.roadmap_preferences.intensity} 강도
              </p>
            </div>
          </div>
          <div className="week-grid">
            {result.weekly_roadmap.map((week) => (
              <article key={week.week} className="week-card">
                <span className="week-label">{week.week}주차</span>
                <strong>{week.goal}</strong>
                <p>{week.practice}</p>
                {week.recommended_titles.length > 0 ? (
                  <ul>
                    {week.recommended_titles.map((title) => (
                      <li key={title}>{title}</li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))}
          </div>
        </div>

        {/* Resource Recommendations */}
        <div className="resource-board reveal-6" id="resources-section">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Curated RAG Resources</p>
              <h3>역량별 추천 자료</h3>
            </div>
            <span className="quiet-pill">DB 기반 검색 · {result.embedding_model}</span>
          </div>
          <div className="resource-columns">
            {result.recommended_resources.map((group) => (
              <article key={group.skill} className="resource-column">
                <h4>
                  {group.skill}
                  <span className={`target-chip ${group.target_type}`}>
                    {group.target_type === "gap" ? "부족" : "보완"}
                  </span>
                </h4>
                {group.recommendations.map((item) => (
                  <a
                    key={item.resource.id}
                    href={item.resource.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <span>{item.resource.type}</span>
                    <strong>{item.resource.title}</strong>
                    <small>
                      {item.resource.level} · 신뢰도 {item.resource.reliability}/5 ·{" "}
                      {item.recommend_score.toFixed(0)}점
                    </small>
                    {item.resource.reason && (
                      <small className="resource-reason">💡 {item.resource.reason}</small>
                    )}
                  </a>
                ))}
              </article>
            ))}
          </div>
        </div>

        {/* Actionable Summary */}
        <ActionableSummary result={result} jdQuality={result.jd_quality ?? ""} />
      </div>
    </div>
  );
}

/* ─── Actionable Summary ────────────────────────────────────────── */
function ActionableSummary({ result, jdQuality }: { result: AnalyzeResponse; jdQuality: string }) {
  const { fit_score, predicted_job, missing_skills, partial_skills, weekly_roadmap, recommended_resources } = result;

  if (jdQuality === "weak") {
    return (
      <div className="actionable-summary reveal-7">
        <p className="eyebrow">다음 할 일</p>
        <p className="summary-lead">공고 품질이 낮아 역량 분석이 불확실합니다.</p>
        <p className="summary-body">공고 본문을 직접 붙여넣어 재분석하면 더 정확한 결과를 얻을 수 있습니다.</p>
      </div>
    );
  }

  const roundedFitScore = Math.round(fit_score);
  const statusLabel =
    roundedFitScore >= 75 ? "지원 가능한 수준입니다" :
    roundedFitScore >= 45 ? "보완 후 지원을 권장합니다" :
    "추가 준비가 필요합니다";

  // Sort by gap_score desc — same order as recommended_resources (backend guarantee)
  const allGaps = [...missing_skills, ...partial_skills].sort((a, b) => b.gap_score - a.gap_score);
  const topGap = allGaps[0] ?? null;
  // Look up the resource for topGap's specific skill to prevent index mismatch
  const topResource = topGap
    ? (recommended_resources.find((r) => r.skill === topGap.skill)?.recommendations[0]?.resource ?? null)
    : null;
  const week1 = weekly_roadmap[0];

  const lines: Array<{ key: string; text: string; lead: boolean }> = [
    { key: "status", lead: true, text: `${predicted_job} 포지션 기준 적합도 ${roundedFitScore}점 — ${statusLabel}.` },
  ];

  if (topGap) {
    const resourceNote = topResource ? ` 추천 자료: 《${topResource.title}》` : "";
    lines.push({ key: "gap", lead: false, text: `가장 먼저 보완할 역량은 ${topGap.skill}입니다.${resourceNote}` });
  } else {
    lines.push({ key: "gap", lead: false, text: "공고 요건을 모두 충족하고 있습니다." });
  }

  if (week1) {
    const practiceNote = week1.practice ? ` — ${week1.practice}` : "";
    lines.push({ key: "week1", lead: false, text: `1주차 목표: ${week1.goal}${practiceNote}` });
  }

  return (
    <div className="actionable-summary reveal-7">
      <p className="eyebrow">다음 할 일</p>
      {lines.map(({ key, text, lead }) => (
        <p key={key} className={lead ? "summary-lead" : "summary-body"}>
          {text}
        </p>
      ))}
    </div>
  );
}

/* ─── Fit Gauge (SVG semicircle) ────────────────────────────────── */
function FitGauge({ score }: { score: number }) {
  const R = 54;
  const cx = 70;
  const cy = 68;
  const startAngle = 180;
  const endAngle = 0;
  const totalAngle = startAngle - endAngle;
  const fillAngle = (score / 100) * totalAngle;

  function polar(angle: number) {
    const rad = (angle * Math.PI) / 180;
    return {
      x: cx + R * Math.cos(rad),
      y: cy - R * Math.sin(rad),
    };
  }

  const start = polar(startAngle);
  const bgEnd = polar(endAngle);
  const fgEnd = polar(startAngle - fillAngle);
  const largeArcFg = fillAngle > 180 ? 1 : 0;

  const bgPath = `M ${start.x} ${start.y} A ${R} ${R} 0 1 1 ${bgEnd.x} ${bgEnd.y}`;
  const fgPath =
    fillAngle <= 0
      ? ""
      : `M ${start.x} ${start.y} A ${R} ${R} 0 ${largeArcFg} 1 ${fgEnd.x} ${fgEnd.y}`;

  return (
    <svg viewBox="0 0 140 76" width="140" height="76" aria-hidden="true">
      <path d={bgPath} fill="none" stroke="#dce8d8" strokeWidth="10" strokeLinecap="round" />
      {fgPath ? (
        <path d={fgPath} fill="none" stroke="#c8e55a" strokeWidth="10" strokeLinecap="round" />
      ) : null}
    </svg>
  );
}

/* ─── Evidence Column ───────────────────────────────────────────── */
function EvidenceColumn({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="evidence-column">
      <h3>{title}</h3>
      {items.length > 0 ? (
        <div>
          {items.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      ) : (
        <p>확인된 항목 없음</p>
      )}
    </div>
  );
}

/* ─── Helpers ───────────────────────────────────────────────────── */
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
  const msg = error instanceof Error ? error.message : "분석 중 오류가 발생했습니다.";
  if (msg.includes("candidate text is too short"))
    return "지원자 자료가 너무 짧습니다. 20자 이상 입력해 주세요.";
  if (msg.includes("job_posting text is too short"))
    return "채용공고 내용이 너무 짧습니다. 20자 이상 입력해 주세요.";
  if (msg.includes("URL 본문") || msg.includes("URL에서"))
    return "URL에서 본문을 가져오지 못했습니다. 직접 붙여넣어 주세요.";
  return msg;
}
