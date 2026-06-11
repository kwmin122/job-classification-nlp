"use client";
import React, { useEffect, useState } from "react";
import * as Ic from "./Icons";

type Stage = "input" | "analyzing" | "results";
type View = "dash" | "report" | "lib" | "road";

interface SidebarProps {
  stage: Stage;
  view: View;
  gapCount: number;
  onNav: (v: View) => void;
}

export function Sidebar({ stage, view, gapCount, onNav }: SidebarProps) {
  const nav = [
    { id: "dash" as View, label: "분석 대시보드", icon: Ic.Grid },
    { id: "report" as View, label: "분석 리포트", icon: Ic.Doc, badge: stage === "results" ? gapCount : null },
    { id: "lib" as View, label: "추천 자료함", icon: Ic.Book },
    { id: "road" as View, label: "학습 로드맵", icon: Ic.Map },
    { id: "hist" as View, label: "지난 분석", icon: Ic.Layers, soon: true },
  ] as Array<{ id: View; label: string; icon: React.FC<{size?: number; sw?: number}>; badge?: number | null; soon?: boolean }>;
  const locked = stage !== "results";
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="mark"><Ic.Target size={20} sw={2}/></div>
        <div>
          <div className="name">역량 핏</div>
          <div className="sub">Career Fit Analyzer</div>
        </div>
      </div>

      <div className="nav-label">분석</div>
      <nav className="nav">
        {nav.map(n => {
          const disabled = !!n.soon || (locked && n.id !== "dash");
          const active = stage === "results" ? view === n.id : n.id === "dash";
          return (
            <button key={n.id}
              className={"nav-item" + (active ? " active" : "") + (disabled ? " disabled" : "")}
              onClick={() => { if (!disabled) onNav(n.id); }}>
              <n.icon size={18}/>
              <span>{n.label}</span>
              {n.badge ? <span className="badge-n tnum">{n.badge}</span> : null}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-spacer"/>
      <div className="side-divider"/>
      <div className="profile">
        <div className="ava">지</div>
        <div>
          <div className="pname">지원자 미리보기</div>
          <div className="pmail">demo@careerfit.io</div>
        </div>
      </div>
    </aside>
  );
}

/* Tooltip */
export function Tip({ text }: { text: string }) {
  return (
    <span className="tip">
      <span className="tip-ico">i</span>
      <span className="tip-body">{text}</span>
    </span>
  );
}

/* Animated count-up number */
export function useCountUp(target: number, run: boolean, dur = 1100): number {
  const [v, setV] = useState(target);
  useEffect(() => {
    // 애니메이션을 안 켤 때는 실제 목표값을 그대로 표시한다(0으로 떨어뜨리지 않음).
    if (!run) { setV(target); return; }
    let raf: number;
    let start: number | null = null;
    let done = false;
    const tick = (t: number) => {
      if (!start) start = t;
      const p = Math.min(1, (t - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setV(target * e);
      if (p < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        done = true;
        setV(target);
      }
    };
    raf = requestAnimationFrame(tick);
    const fb = setTimeout(() => { if (!done) setV(target); }, dur + 250);
    return () => { cancelAnimationFrame(raf); clearTimeout(fb); };
  }, [target, run, dur]);
  return v;
}
