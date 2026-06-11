"use client";
import React, { useEffect, useState } from "react";
import * as Ic from "./Icons";

const STAGES = [
  "채용공고 본문 확인",
  "지원자 자료 확인",
  "요구 역량 분석",
  "지원자 경험 근거 분석",
  "부족 역량 계산",
  "추천 자료 검색",
  "학습 로드맵 생성",
  "분석 리포트 작성",
];

interface AnalyzingViewProps {
  onDone: () => void;
}

export function AnalyzingView({ onDone }: AnalyzingViewProps) {
  const [cur, setCur] = useState(0);

  useEffect(() => {
    if (cur >= STAGES.length) {
      const t = setTimeout(onDone, 650);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setCur(c => c + 1), cur === 0 ? 1150 : 720 + Math.random() * 360);
    return () => clearTimeout(t);
  }, [cur, onDone]);

  const pct = Math.min(100, Math.round((cur / STAGES.length) * 100));
  const stateOf = (i: number) => {
    if (i < cur) return "done";
    if (i === cur) return "run";
    return "todo";
  };

  return (
    <div className="analyzing fade-in">
      <div className="card pad-card az-card">
        <div className="az-top">
          <div className="az-spin"><Ic.Spark size={20}/></div>
          <div>
            <h3>자료를 분석하고 있어요</h3>
            <p>채용공고 요구 역량과 지원자 자료의 근거를 맞춰보는 중입니다</p>
          </div>
          <div className="az-pct tnum">{pct}<small>%</small></div>
        </div>
        <div className="az-bar"><span style={{ width: pct + "%" }}/></div>

        <ol className="timeline">
          {STAGES.map((s, i) => {
            const st = stateOf(i);
            return (
              <li key={i} className={"tl-item " + st}>
                <span className="tl-node">
                  {st === "done" ? <Ic.Check size={13} sw={2.6}/>
                    : st === "run" ? <span className="tl-pulse"/>
                    : <span className="tl-dot"/>}
                </span>
                <span className="tl-label">{s}</span>
                {st === "run" && <span className="tl-tag run">진행 중</span>}
                {st === "done" && <span className="tl-tag ok">완료</span>}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
