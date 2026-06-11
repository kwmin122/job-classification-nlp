"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom";
import { Sidebar } from "@/components/Sidebar";
import { InputView } from "@/components/InputView";
import type { FormState } from "@/components/InputView";
import { AnalyzingView } from "@/components/AnalyzingView";
import { SummaryRow, ScorePanel } from "@/components/ResultsSummary";
import { CompetencyTabs, ExcludedSection } from "@/components/ResultsCompetency";
import { ResourcesView, RoadmapView, ReportView } from "@/components/ResultsRecos";
import { analyze } from "@/lib/api";
import type { UiBlock, UiMetComp, UiPartialComp, AnalyzeResponse } from "@/lib/types";
import * as Ic from "@/components/Icons";

/* ─── types ─────────────────────────────────────────────────────── */
type Stage = "input" | "analyzing" | "results";
type View = "dash" | "report" | "lib" | "road";
type PeekableItem = UiMetComp | UiPartialComp;

/* ─── EvidencePeek modal ─────────────────────────────────────────── */
interface EvidencePeekProps {
  item: PeekableItem;
  onClose: () => void;
}
function EvidencePeek({ item, onClose }: EvidencePeekProps) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [onClose]);
  return ReactDOM.createPortal(
    <div className="peek-backdrop" onClick={onClose}>
      <div className="peek-card peek-in" onClick={e => e.stopPropagation()}>
        <div className="peek-head">
          <b>{item.skill}</b>
          <button className="icon-act" onClick={onClose}><Ic.X size={17}/></button>
        </div>
        <div className="peek-body">
          <div className="peek-ev"><Ic.Quote size={14}/>&ldquo;{item.evidence}&rdquo;</div>
          {"verdict" in item && (
            <div className="peek-note"><Ic.Info size={14}/>{(item as UiPartialComp).verdict}</div>
          )}
          <div className="peek-source">출처: {item.source}</div>
        </div>
        <div className="peek-cov">
          <span className="peek-label">충족도</span>
          <div className="score-track" style={{ flex: 1 }}>
            <span className={"coverage" in item && (item as UiMetComp).coverage >= 80 ? "good" : "warn"}
              style={{ width: item.coverage + "%" }}/>
          </div>
          <span className="peek-pct tnum">{item.coverage}%</span>
        </div>
      </div>
    </div>,
    document.body
  );
}

/* ─── DashboardView ───────────────────────────────────────────────── */
interface DashboardViewProps {
  d: UiBlock;
  run: boolean;
  onJump: (skill: string, target: string) => void;
  onPeek: (item: PeekableItem) => void;
}
function DashboardView({ d, run, onJump, onPeek }: DashboardViewProps) {
  return (
    <div className="view fade-in">
      <div className="view-head">
        <div>
          <h2>분석 대시보드</h2>
          <p className="view-sub">{d.job.title} · {d.job.group} · 자료 기준 핏 {d.summary.fit}점</p>
        </div>
        <span className="spacer"/>
        <div className="pill good"><span className="pdot"/>분석 완료</div>
      </div>
      <div className="view-body">
        <SummaryRow d={d} run={run}/>
        <div className="dash-row">
          <ScorePanel d={d} run={run}/>
          <CompetencyTabs d={d} onJump={onJump} onPeek={onPeek}/>
        </div>
        <ExcludedSection d={d}/>
      </div>
    </div>
  );
}

/* ─── helpers ─────────────────────────────────────────────────────── */
const INIT_FORM: FormState = {
  jd: "",
  jdSkills: [],
  cl: "",
  files: [],
  jdStatus: null,
  opts: { weeks: "4주", level: "기초", intensity: "보통" },
};

function weeksNum(s: string): 2 | 4 | 8 | 12 {
  const n = parseInt(s);
  if (n === 2 || n === 4 || n === 8 || n === 12) return n;
  return 4;
}
function levelKo(s: string): "입문" | "기초" | "실무" | "심화" {
  if (s === "입문" || s === "기초" || s === "실무" || s === "심화") return s;
  return "기초";
}
function intensityKo(s: string): "가볍게" | "보통" | "집중" {
  if (s === "가볍게" || s === "보통" || s === "집중") return s;
  return "보통";
}

/* ─── Page ────────────────────────────────────────────────────────── */
export default function Home() {
  const [stage, setStage] = useState<Stage>("input");
  const [view, setView] = useState<View>("dash");
  const [form, setForm] = useState<FormState>(INIT_FORM);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [runAnim, setRunAnim] = useState(false);
  const [highlight, setHighlight] = useState<string | null>(null);
  const [peek, setPeek] = useState<PeekableItem | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [animDone, setAnimDone] = useState(false);
  const pendingJump = useRef<{ skill: string; target: string } | null>(null);

  /* Start analysis */
  const startAnalysis = useCallback(async () => {
    if (!form.jd.trim() || !form.cl.trim()) {
      setApiError("채용공고와 자소서를 모두 입력해 주세요. (공고는 URL 불러오기 또는 직접 입력)");
      return;
    }
    setApiError(null);
    setResult(null);
    setAnimDone(false);
    setStage("analyzing");
    try {
      const res = await analyze({
        job_posting: { source_type: "text", text: form.jd, structured_skills: form.jdSkills },
        candidate_materials: [{ source_type: "text", label: "자소서", text: form.cl }],
        roadmap_preferences: {
          duration_weeks: weeksNum(form.opts.weeks),
          difficulty: levelKo(form.opts.level),
          intensity: intensityKo(form.opts.intensity),
        },
      });
      setResult(res);
    } catch (e) {
      setApiError(e instanceof Error ? e.message : String(e));
      setStage("input");
    }
  }, [form]);

  /* AnalyzingView calls onDone when its animation finishes (그 자체로 화면 전환하지 않음) */
  const finishAnalysis = useCallback(() => { setAnimDone(true); }, []);

  /* 결과가 도착했고 + 진행 애니메이션도 끝났을 때만 결과 화면으로 전환.
     (API가 느려도 멈추지 않고, 결과가 준비될 때까지 분석 화면 유지) */
  useEffect(() => {
    if (stage === "analyzing" && animDone && result) {
      setStage("results");
      setView("dash");
      setRunAnim(false);
      const t = setTimeout(() => setRunAnim(true), 80);
      return () => clearTimeout(t);
    }
  }, [stage, animDone, result]);

  /* Jump to another view, optionally highlight a resource card */
  const jump = useCallback((skill: string, target: string) => {
    if (target === "lib") {
      pendingJump.current = { skill, target };
      setView("lib");
      setHighlight(skill);
      // clear highlight after scroll
      setTimeout(() => {
        const el = document.getElementById("res-" + skill);
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
        setTimeout(() => setHighlight(null), 1800);
      }, 120);
    } else {
      setView(target as View);
    }
  }, []);

  const restart = useCallback(() => {
    setStage("input");
    setView("dash");
    setResult(null);
    setRunAnim(false);
    setHighlight(null);
    setApiError(null);
  }, []);

  const ui = result?.ui ?? null;

  return (
    <div className="shell">
      <Sidebar
        stage={stage}
        view={view}
        gapCount={ui?.summary.gapCount ?? 0}
        onNav={(v) => setView(v)}
      />
      <main className="panel">
        {/* ── Input ── */}
        {stage === "input" && (
          <>
            <div className="panel-header">
              <div className="panel-title-row">
                <h1>Career Compass</h1>
                <p>채용공고가 요구하는 역량과 내 자료를 맞춰, 지금 내 위치와 다음에 채울 역량을 알려드립니다</p>
              </div>
            </div>
            {apiError && (
              <div className="status bad" style={{ margin: "0 0 16px" }}>
                <Ic.Alert size={15}/>서버 오류: {apiError}
              </div>
            )}
            <InputView form={form} setForm={setForm} onStart={startAnalysis}/>
          </>
        )}

        {/* ── Analyzing ── */}
        {stage === "analyzing" && (
          <AnalyzingView onDone={finishAnalysis}/>
        )}

        {/* ── Results ── */}
        {stage === "results" && ui && (
          <>
            {/* job header bar */}
            <div className="result-header">
              <div className="rh-job">
                <div className="icon-badge"><Ic.Target size={18}/></div>
                <div>
                  <div className="rh-title">{ui.job.title}</div>
                  <div className="rh-meta">{ui.job.group} · {ui.job.source}</div>
                </div>
              </div>
              <div className="rh-tags">
                {ui.job.core.slice(0, 4).map((k, i) => (
                  <span className="mini-chip" key={i}>{k}</span>
                ))}
              </div>
              <span className="spacer"/>
              <button className="btn ghost sm" onClick={restart}><Ic.Refresh size={14}/>다시 분석</button>
            </div>

            {/* nav tabs (mobile/narrow) */}
            <div className="view-tabs">
              {(["dash", "report", "lib", "road"] as View[]).map(v => (
                <button key={v} className={"view-tab" + (view === v ? " on" : "")} onClick={() => setView(v)}>
                  {v === "dash" ? "대시보드" : v === "report" ? "리포트" : v === "lib" ? "자료함" : "로드맵"}
                </button>
              ))}
            </div>

            {view === "dash" && (
              <DashboardView d={ui} run={runAnim} onJump={jump} onPeek={setPeek}/>
            )}
            {view === "report" && (
              <ReportView d={ui} onRestart={restart}/>
            )}
            {view === "lib" && (
              <ResourcesView d={ui} highlight={highlight}/>
            )}
            {view === "road" && (
              <RoadmapView d={ui} highlight={highlight}/>
            )}
          </>
        )}

        {/* ── Results but no ui block (fallback) ── */}
        {stage === "results" && !ui && (
          <div className="analyzing fade-in">
            <div className="card pad-card" style={{ textAlign: "center", padding: 48 }}>
              <Ic.Alert size={28}/>
              <p style={{ marginTop: 12 }}>UI 블록이 없습니다. 백엔드 응답을 확인해 주세요.</p>
              <button className="btn dark sm" style={{ marginTop: 16 }} onClick={restart}>
                <Ic.Refresh size={14}/>다시 시작
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Evidence peek modal */}
      {peek && <EvidencePeek item={peek} onClose={() => setPeek(null)}/>}
    </div>
  );
}
