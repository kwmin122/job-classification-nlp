"use client";
import React, { useState } from "react";
import * as Ic from "./Icons";
import type { UiBlock, UiMetComp, UiPartialComp, UiGapComp, UiAdjComp, GapType } from "../lib/types";

const GAP_META: Record<GapType, { label: string; tone: string; desc: string }> = {
  learning:   { label: "학습 부족", tone: "bad",  desc: "실제 학습·경험 자체가 부족한 것으로 추정됩니다." },
  evidence:   { label: "근거 부족", tone: "warn", desc: "역량은 있을 수 있으나 자료에 근거 문장이 부족합니다." },
  expression: { label: "표현 부족", tone: "info", desc: "경험은 있으나 기술명·역할·성과 표현이 불명확합니다." },
  explicit:   { label: "명시적 부족", tone: "neutral", desc: "지원자가 자료에서 직접 부족하다고 언급했습니다." },
};

interface MetRowProps { c: UiMetComp; onPeek: (c: UiMetComp) => void; }
function MetRow({ c, onPeek }: MetRowProps) {
  return (
    <button className="crow" onClick={() => onPeek(c)}>
      <div className="crow-top">
        <b>{c.skill}</b>
        <span className="pill good"><span className="pdot"/>충족 {c.coverage}%</span>
      </div>
      <div className="crow-ev"><Ic.Quote size={13}/><span>{c.evidence}</span></div>
      <div className="cov-track"><span className="good" style={{ width: c.coverage + "%" }}/></div>
    </button>
  );
}

interface PartialRowProps { c: UiPartialComp; onPeek: (c: UiPartialComp) => void; }
function PartialRow({ c, onPeek }: PartialRowProps) {
  return (
    <button className="crow" onClick={() => onPeek(c)}>
      <div className="crow-top">
        <b>{c.skill}</b>
        <span className="pill warn"><span className="pdot"/>부분 충족 {c.coverage}%</span>
      </div>
      <div className="crow-note"><Ic.Info size={13}/>{c.verdict}</div>
      <div className="cov-track"><span className="warn" style={{ width: c.coverage + "%" }}/></div>
    </button>
  );
}

interface GapRowProps { c: UiGapComp; onJump: (skill: string, target: string) => void; }
function GapRow({ c, onJump }: GapRowProps) {
  const m = GAP_META[c.gap] || GAP_META.learning;
  return (
    <div className="crow gap">
      <div className="crow-top">
        <b>{c.skill}</b>
        <span className={"pill " + m.tone}><span className="pdot"/>{m.label}</span>
        <button className="jump" onClick={() => onJump(c.skill, "lib")}>추천 자료 <Ic.ArrowRight size={13}/></button>
      </div>
      <div className="crow-note"><Ic.Info size={13}/>{c.note}</div>
    </div>
  );
}

interface AdjRowProps { a: UiAdjComp; }
function AdjRow({ a }: AdjRowProps) {
  return (
    <div className="crow">
      <div className="crow-top">
        <b>{a.cat}</b>
        <span className="adj-lvl tnum">{a.level}</span>
      </div>
      <div className="cov-track"><span className="lime" style={{ width: a.level + "%" }}/></div>
      <div className="crow-note sub">{a.note}</div>
    </div>
  );
}

type PeekableItem = UiMetComp | UiPartialComp;

interface CompetencyTabsProps {
  d: UiBlock;
  onJump: (skill: string, target: string) => void;
  onPeek: (item: PeekableItem) => void;
}
export function CompetencyTabs({ d, onJump, onPeek }: CompetencyTabsProps) {
  const comp = d.competencies;
  const reqTotal = comp.met.length + comp.partial.length + comp.gap.length;
  const tabs = [
    { id: "req", label: "요구 역량", n: reqTotal, tone: "neutral" },
    { id: "met", label: "보유", n: comp.met.length, tone: "good" },
    { id: "partial", label: "부분", n: comp.partial.length, tone: "warn" },
    { id: "gap", label: "부족", n: comp.gap.length, tone: "bad" },
    { id: "adjacent", label: "직무 외 강점", n: comp.adjacent.length, tone: "info" },
  ];
  const [tab, setTab] = useState("req");
  return (
    <div className="dash-card comp-panel">
      <div className="dash-card-head">
        <h2>공고 요구 역량 vs 내 역량</h2>
        <span className="hint">공고가 요구한 역량별로 보유·부분·부족을 한눈에. 근거 문장을 누르면 원문 위치를 봐요</span>
      </div>
      <div className="tabs">
        {tabs.map(t => (
          <button key={t.id} className={"tab" + (tab === t.id ? " on" : "")} onClick={() => setTab(t.id)}>
            {t.label}<span className={"tab-n " + t.tone}>{t.n}</span>
          </button>
        ))}
      </div>

      <div className="comp-scroll">
        {tab === "req" && (
          <div className="tabpane" key="req">
            <div className="req-summary">
              공고가 요구한 <b>{reqTotal}개</b> 역량 · 보유 <b className="t-good">{comp.met.length}</b> · 부분 <b className="t-warn">{comp.partial.length}</b> · 부족 <b className="t-bad">{comp.gap.length}</b>
            </div>
            <div className="comp-list">
              {comp.met.map((c, i) => <MetRow key={"m" + i} c={c} onPeek={onPeek}/>)}
              {comp.partial.map((c, i) => <PartialRow key={"p" + i} c={c} onPeek={onPeek}/>)}
              {comp.gap.map((c, i) => <GapRow key={"g" + i} c={c} onJump={onJump}/>)}
              {reqTotal === 0 && <div className="empty-note">공고에서 요구 역량을 추출하지 못했습니다. URL로 공고를 불러오거나 본문을 더 자세히 넣어 주세요.</div>}
            </div>
          </div>
        )}
        {tab === "met" && <div className="comp-list tabpane" key="met">{comp.met.map((c, i) => <MetRow key={i} c={c} onPeek={onPeek}/>)}</div>}
        {tab === "partial" && <div className="comp-list tabpane" key="partial">{comp.partial.map((c, i) => <PartialRow key={i} c={c} onPeek={onPeek}/>)}</div>}
        {tab === "gap" && <div className="comp-list tabpane" key="gap">{comp.gap.map((c, i) => <GapRow key={i} c={c} onJump={onJump}/>)}</div>}
        {tab === "adjacent" && (
          <div className="tabpane" key="adjacent">
            <div className="adj-banner"><Ic.Bolt size={14}/><span>PM·협업·운영처럼 공고의 <b>핵심 기술은 아니지만</b> 참고할 강점입니다. 적합도 점수에는 반영되지 않습니다.</span></div>
            <div className="comp-list">{comp.adjacent.map((a, i) => <AdjRow key={i} a={a}/>)}</div>
          </div>
        )}
      </div>
    </div>
  );
}

interface ExcludedSectionProps { d: UiBlock; defaultOpen?: boolean; }
export function ExcludedSection({ d, defaultOpen }: ExcludedSectionProps) {
  const [open, setOpen] = useState(!!defaultOpen);
  return (
    <div className="excluded card" id="excluded">
      <button className="ex-head" onClick={() => setOpen(o => !o)}>
        <div className="icon-badge" style={{ background: "#EEF0F2", color: "var(--t2)", width: 38, height: 38 }}><Ic.Filter size={17}/></div>
        <div className="ex-title">
          <h3>근거로 사용하지 않은 문장 <span className="ex-count">{d.excluded.length}</span></h3>
          <p>사회 이슈·지원동기·포부 등은 실제 수행 경험이 아니라 역량 근거에서 제외했어요</p>
        </div>
        <span className={"ex-chev" + (open ? " open" : "")}><Ic.Chevron size={18}/></span>
      </button>
      {open && (
        <div className="ex-body tabpane">
          {d.excluded.map((e, i) => (
            <div className="ex-item" key={i}>
              <div className="ex-tag">{e.tag}</div>
              <div className="ex-quote">&ldquo;{e.text}&rdquo;</div>
              <div className="ex-reason"><Ic.Info size={13}/>{e.reason}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
