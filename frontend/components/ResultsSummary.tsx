"use client";
import React from "react";
import * as Ic from "./Icons";
import { Tip, useCountUp } from "./Sidebar";
import type { UiBlock, UiScoreBreakdown } from "../lib/types";

interface GaugeProps { value: number; size?: number; stroke?: number; color: string; }
export function Gauge({ value, size = 54, stroke = 6, color }: GaugeProps) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - value / 100);
  return (
    <svg width={size} height={size} className="gauge">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#EDEFF1" strokeWidth={stroke}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={stroke}
        strokeLinecap="round" strokeDasharray={c} strokeDashoffset={off}
        transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(.22,.61,.36,1)" }}/>
    </svg>
  );
}

interface SummaryRowProps { d: UiBlock; run: boolean; }
export function SummaryRow({ d, run }: SummaryRowProps) {
  const fit = useCountUp(d.summary.fit, run);
  const conf = useCountUp(d.summary.predictedConfidence, run);
  const gaps = useCountUp(d.summary.gapCount, run, 900);
  return (
    <div className="summary-row">
      <div className="card stat">
        <div className="icon-badge"><Ic.Target size={19}/></div>
        <div className="stat-body">
          <div className="stat-kicker">예측 직무</div>
          <div className="stat-main job">{d.summary.predictedJob}</div>
          <div className="pill good" style={{ marginTop: 6 }}><span className="pdot"/>신뢰도 {Math.round(conf)}%</div>
        </div>
      </div>

      <div className="card stat">
        <Gauge value={run ? d.summary.fit : 0} color="#D98A24"/>
        <div className="stat-body">
          <div className="stat-kicker">현재 자료 기준 적합도</div>
          <div className="stat-main tnum">{Math.round(fit)}<small>/100</small></div>
          <div className="stat-sub">보완 여지가 큰 구간</div>
        </div>
      </div>

      <div className="card stat">
        <div className="icon-badge" style={{ background: "var(--bad-bg)", color: "var(--bad)" }}><Ic.Alert size={19}/></div>
        <div className="stat-body">
          <div className="stat-kicker">부족 역량</div>
          <div className="stat-main tnum">{Math.round(gaps)}<small>개</small></div>
          <div className="stat-sub">근거·표현·학습 부족 포함</div>
        </div>
      </div>

      <div className="card stat dark">
        <div className="icon-badge" style={{ background: "rgba(255,255,255,.12)", color: "#fff" }}><Ic.Map size={19}/></div>
        <div className="stat-body">
          <div className="stat-kicker">추천 학습 기간</div>
          <div className="stat-main tnum">{d.summary.weeks}<small>주</small></div>
          <div className="stat-sub">난이도 {d.summary.level} · {d.summary.intensity}</div>
        </div>
      </div>
    </div>
  );
}

interface ScoreRowProps { item: UiScoreBreakdown; run: boolean; delay: number; }
function ScoreRow({ item, run, delay }: ScoreRowProps) {
  const v = useCountUp(item.value, run, 1000);
  const color = item.tone === "good" ? "var(--good)"
    : item.tone === "warn" ? "var(--warn)"
    : item.tone === "bad" ? "var(--bad)"
    : "var(--info)";
  return (
    <div className="score-row">
      <div className="score-row-head">
        <span className="score-label">{item.label}<Tip text={item.tip}/></span>
        {item.weight && <span className="score-weight">가중치 {item.weight}</span>}
        <span className="score-val tnum" style={{ color }}>{Math.round(v)}<small>{item.isCount ? item.unit : ""}</small></span>
      </div>
      {!item.isCount
        ? <div className="score-track"><span style={{ width: (run ? item.value : 0) + "%", background: color, transitionDelay: delay + "ms" }}/></div>
        : <div className="score-flag">표현만 보완하면 점수 상승 여지가 있어요</div>}
    </div>
  );
}

interface ScorePanelProps { d: UiBlock; run: boolean; }
export function ScorePanel({ d, run }: ScorePanelProps) {
  return (
    <div className="dash-card score-card">
      <div className="dash-card-head">
        <h2>적합도 점수 상세</h2>
        <span className="hint">하나의 점수가 아니라, 어디서 점수가 나뉘는지 분해해 보여줍니다</span>
      </div>
      <div className="score-list">
        {d.scoreBreakdown.map((it, i) => <ScoreRow key={it.key} item={it} run={run} delay={i * 90}/>)}
      </div>
      <div className="disclaimer">
        <Ic.Info size={15}/>
        이 점수는 지원자의 실제 능력을 단정하지 않고, 현재 제출한 자료에 드러난 근거를 기준으로 계산됩니다. 자소서에 적힌 성과 수치는 검증된 결과가 아니라 '자소서상 주장'으로만 반영됩니다.
      </div>
    </div>
  );
}
