"use client";
import React, { useState } from "react";
import * as Ic from "./Icons";
import type { UiBlock, UiResourceGroup, UiRoadmapWeek, GapType } from "../lib/types";

const GAP_META: Record<GapType, { label: string; tone: string }> = {
  learning:   { label: "학습 부족", tone: "bad" },
  evidence:   { label: "근거 부족", tone: "warn" },
  expression: { label: "표현 부족", tone: "info" },
  explicit:   { label: "명시적 부족", tone: "neutral" },
};

const KIND_TONE: Record<string, string> = {
  "공식문서": "info", "강의": "good", "블로그": "neutral", "유튜브": "bad", "실습자료": "warn"
};

interface ResourceItemProps {
  it: UiResourceGroup["items"][number];
  onAdd: () => void;
  added: boolean;
}
function ResourceItem({ it, onAdd, added }: ResourceItemProps) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return (
    <div className="res-item dismissed">
      <span>추천에서 숨김 처리됨</span>
      <button className="link-btn" onClick={() => setDismissed(false)}>되돌리기</button>
    </div>
  );
  return (
    <div className="res-item">
      <div className="res-main">
        <div className="res-title">{it.title}</div>
        <div className="res-tags">
          <span className={"pill " + (KIND_TONE[it.kind] || "neutral")} style={{ fontSize: 10.5, padding: "3px 8px" }}>{it.kind}</span>
          <span className="rt">{it.level}</span>
          <span className={"rt " + (it.price === "무료" ? "free" : "paid")}>{it.price}</span>
          <span className="rt trust"><Ic.CheckCircle size={12}/>신뢰도 {it.trust}</span>
        </div>
        <div className="res-why">{it.why}</div>
      </div>
      <div className="res-actions">
        <button className="btn dark sm" onClick={() => {}}><Ic.ArrowUpRight size={14}/>자료 열기</button>
        <button className={"icon-act" + (added ? " on" : "")} title="로드맵에 추가" onClick={onAdd}>
          {added ? <Ic.Check size={15} sw={2.6}/> : <Ic.Pin size={15}/>}
        </button>
        <button className="icon-act" title="대체 자료" onClick={() => {}}><Ic.Swap size={15}/></button>
        <button className="icon-act" title="관심 없음" onClick={() => setDismissed(true)}><Ic.X size={15}/></button>
      </div>
    </div>
  );
}

interface ResourceCardProps { group: UiResourceGroup; highlight: string | null; }
function ResourceCard({ group, highlight }: ResourceCardProps) {
  const m = GAP_META[group.gap] || GAP_META.learning;
  const [added, setAdded] = useState<Record<number, boolean>>({});
  const hot = highlight === group.skill;
  return (
    <div className={"res-card card" + (hot ? " hot" : "")} id={"res-" + group.skill}>
      <div className="res-head">
        <div className="res-skill">{group.skill}</div>
        <div className={"pill " + m.tone}><span className="pdot"/>{m.label}</div>
        <span className="res-count">추천 {group.items.length}</span>
      </div>
      <div className="res-list">
        {group.items.map((it, i) => (
          <ResourceItem key={i} it={it} added={!!added[i]} onAdd={() => setAdded(a => ({ ...a, [i]: !a[i] }))}/>
        ))}
      </div>
    </div>
  );
}

interface ResourcesViewProps { d: UiBlock; highlight: string | null; }
export function ResourcesView({ d, highlight }: ResourcesViewProps) {
  return (
    <div className="view fade-in">
      <div className="view-head">
        <div>
          <h2>추천 학습자료</h2>
          <p className="view-sub">부족 역량별로 가장 도움이 될 자료 Top 3 · 카드를 눌러 로드맵에 담거나 대체 자료를 볼 수 있어요</p>
        </div>
      </div>
      <div className="view-body">
        <div className="res-grid">
          {d.resources.map((g, i) => <ResourceCard key={i} group={g} highlight={highlight}/>)}
        </div>
      </div>
    </div>
  );
}

/* ─── Roadmap ──────────────────────────────────────────────────── */
const EXTRA_WEEKS: Omit<UiRoadmapWeek, "week">[] = [
  { goal: "심화 학습 및 복습", skills: ["전반"], res: "이전 자료 복습", task: "학습 내용 정리 및 복습", output: "복습 정리 노트" },
  { goal: "프로젝트 확장 및 개선", skills: ["전반"], res: "—", task: "기존 프로젝트 기능 확장", output: "확장된 결과물" },
  { goal: "포트폴리오·자소서 정리", skills: ["문서화"], res: "STAR 작성 가이드", task: "경험을 채용 키워드 중심으로 재작성", output: "보완된 자소서 초안" },
  { goal: "모의 면접 대비", skills: ["전반"], res: "기술 면접 질문 모음", task: "예상 질문 20개 답변 준비", output: "면접 대비 노트" },
];

function buildWeeks(base: UiRoadmapWeek[], target: number): UiRoadmapWeek[] {
  if (target <= base.length) return base.slice(0, target);
  const out = [...base];
  let i = 0;
  while (out.length < target) { out.push(EXTRA_WEEKS[i % EXTRA_WEEKS.length] as UiRoadmapWeek); i++; }
  return out.map((w, idx) => ({ ...w, week: idx + 1 }));
}

interface WeekCardProps {
  w: UiRoadmapWeek;
  open: boolean;
  onToggle: () => void;
  done: boolean;
  onDone: () => void;
}
function WeekCard({ w, open, onToggle, done, onDone }: WeekCardProps) {
  return (
    <div className={"week-card" + (open ? " open" : "") + (done ? " done" : "")}>
      <button className="week-head" onClick={onToggle}>
        <span className="week-no">{done ? <Ic.Check size={15} sw={2.8}/> : w.week}<small>주차</small></span>
        <span className="week-goal">{w.goal}</span>
        <span className="week-skills">{w.skills.map((s, i) => <span className="mini-chip" key={i}>{s}</span>)}</span>
        <span className={"ex-chev" + (open ? " open" : "")}><Ic.Chevron size={17}/></span>
      </button>
      {open && (
        <div className="week-body tabpane">
          <div className="wk-row"><span className="wk-k">추천 자료</span><span className="wk-v">{w.res}</span></div>
          <div className="wk-row"><span className="wk-k">실습 과제</span><span className="wk-v">{w.task}</span></div>
          <div className="wk-row"><span className="wk-k">예상 산출물</span><span className="wk-v out">{w.output}</span></div>
          <div className="wk-actions">
            <button className={"btn sm " + (done ? "ghost" : "lime")} onClick={onDone}>
              {done ? <><Ic.Refresh size={13}/>완료 취소</> : <><Ic.Check size={14}/>완료 표시</>}
            </button>
            <button className="btn ghost sm"><Ic.ArrowUpRight size={13}/>자료 열기</button>
          </div>
        </div>
      )}
    </div>
  );
}

interface RoadmapViewProps { d: UiBlock; highlight: string | null; }
export function RoadmapView({ d, highlight }: RoadmapViewProps) {
  const [weeks, setWeeks] = useState(d.summary.weeks);
  const list = buildWeeks(d.roadmap, weeks);
  const [open, setOpen] = useState<Record<number, boolean>>({ 1: true });
  const [done, setDone] = useState<Record<number, boolean>>({});
  const doneN = Object.values(done).filter(Boolean).length;
  return (
    <div className="view fade-in">
      <div className="view-head">
        <div>
          <h2>주차별 학습 로드맵</h2>
          <p className="view-sub">{doneN}/{list.length}주차 완료 · 각 주차를 눌러 펼쳐 보세요</p>
        </div>
        <span className="spacer"/>
        <div className="seg small">
          {[2, 4, 8, 12].map(w => (
            <button key={w} className={"seg-btn" + (weeks === w ? " on" : "")} onClick={() => setWeeks(w)}>{w}주</button>
          ))}
        </div>
      </div>
      <div className="view-body">
        <div className="week-list">
          {list.map(w => (
            <WeekCard key={w.week} w={w} open={!!open[w.week]} done={!!done[w.week]}
              onToggle={() => setOpen(o => ({ ...o, [w.week]: !o[w.week] }))}
              onDone={() => setDone(s => ({ ...s, [w.week]: !s[w.week] }))}/>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Report ───────────────────────────────────────────────────── */
interface ReportBlockProps { title: string; items: string[]; accent?: string; }
function ReportBlock({ title, items, accent }: ReportBlockProps) {
  if (!items || items.length === 0) return null;
  return (
    <div className="rep-block">
      <div className={"rep-bar " + (accent || "")}/>
      <div className="rep-content">
        <h4>{title}</h4>
        <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul>
      </div>
    </div>
  );
}

interface ReportViewProps { d: UiBlock; onRestart: () => void; }
export function ReportView({ d, onRestart }: ReportViewProps) {
  const r = d.report;
  const [copied, setCopied] = useState(false);
  const copy = () => {
    const txt = `[역량 분석 리포트]\n\n■ 전체 요약\n${r.summary}\n\n■ 강점\n${r.strengths.map(s => "- " + s).join("\n")}\n\n■ 부족 역량\n${r.gaps.map(s => "- " + s).join("\n")}\n\n■ 표현 보완\n${r.expression.map(s => "- " + s).join("\n")}\n\n■ 추천 학습 순서\n${r.order.join("\n")}\n\n■ 주의사항\n${r.caution.map(s => "- " + s).join("\n")}`;
    navigator.clipboard?.writeText(txt); setCopied(true); setTimeout(() => setCopied(false), 1600);
  };
  return (
    <div className="view fade-in">
      <div className="view-head">
        <div>
          <h2>자연어 분석 리포트</h2>
          <p className="view-sub">읽으면 바로 행동할 수 있게 정리한 요약</p>
        </div>
        <span className="spacer"/>
        <div className="rep-actions">
          <button className="btn sm" onClick={copy}>{copied ? <><Ic.Check size={14}/>복사됨</> : <><Ic.Copy size={14}/>복사</>}</button>
          <button className="btn sm"><Ic.Download size={14}/>Markdown</button>
          <button className="btn sm"><Ic.Pdf size={14}/>PDF</button>
          <button className="btn dark sm" onClick={onRestart}><Ic.Refresh size={14}/>다시 분석</button>
        </div>
      </div>
      <div className="view-body">
        <div className="card report">
          <div className="rep-summary">
            <div className="icon-badge pink"><Ic.Doc size={19}/></div>
            <p>{r.summary}</p>
          </div>
          <div className="rep-grid">
            <ReportBlock title="강점" items={r.strengths} accent="good"/>
            <ReportBlock title="부족 역량" items={r.gaps} accent="bad"/>
            <ReportBlock title="자소서 표현 보완 방향" items={r.expression} accent="info"/>
            <ReportBlock title="추천 학습 순서" items={r.order} accent="lime"/>
          </div>
          <div className="rep-caution">
            <Ic.Info size={15}/>
            <div><b>주의사항</b><ul>{r.caution.map((c, i) => <li key={i}>{c}</li>)}</ul></div>
          </div>
        </div>
      </div>
    </div>
  );
}
