"use client";
import React, { useRef, useState } from "react";
import * as Ic from "./Icons";
import { Tip } from "./Sidebar";
import { extractJobPostingFromUrl } from "../lib/api";

const SAMPLE_JD = `[백엔드 개발자 채용]
· Java, Spring Boot 기반 REST API 설계 및 개발
· RDBMS(PostgreSQL) 및 SQL 기반 데이터 처리
· Docker 기반 배포 및 운영 환경 이해
· Git 협업, 코드 리뷰 문화에 익숙하신 분`;

const SAMPLE_CL = `[지원동기] 어릴 때부터 무언가를 만드는 일을 좋아해 자연스럽게 개발자의 꿈을 키웠습니다.
[직무역량] 로그 분석 자동화 프로젝트를 주도하여 일 평균 처리 시간을 40% 단축했습니다. 5인 팀에서 브랜치 전략과 코드 리뷰 규칙을 정리하고 PR 기반 협업을 운영했습니다. 데이터베이스 과목을 이수했고 정규화와 인덱스 개념을 학습했습니다. SQL은 아직 기본 쿼리 수준이라 경험이 부족합니다.
[사회 이슈] AI 기술은 사회적 책임을 가지고 윤리적으로 활용되어야 한다고 생각합니다.
[입사 후 포부] 입사 후에는 회사와 함께 성장하며 최고의 백엔드 개발자가 되겠습니다.`;

interface SegProps {
  value: string;
  onChange: (v: string) => void;
  options: Array<{ v: string; label: string }>;
}
function Seg({ value, onChange, options }: SegProps) {
  return (
    <div className="seg" role="tablist">
      {options.map(o => (
        <button key={o.v} role="tab" aria-selected={value === o.v}
          className={"seg-btn" + (value === o.v ? " on" : "")}
          onClick={() => onChange(o.v)}>{o.label}</button>
      ))}
    </div>
  );
}

interface JdStatus { tone: "good" | "warn" | "bad"; msg: string; }

interface JobCardProps {
  jd: string;
  setJd: (v: string) => void;
  jdStatus: JdStatus | null;
  setJdStatus: (s: JdStatus | null) => void;
}
function JobCard({ jd, setJd, jdStatus, setJdStatus }: JobCardProps) {
  const [tab, setTab] = useState("text");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadMsg, setLoadMsg] = useState("");
  const [showText, setShowText] = useState(false);

  const load = async () => {
    if (tab === "url") {
      if (!url.trim() || loading) return;
      setLoading(true);
      setShowText(false);
      setJdStatus(null);
      // OCR(이미지 공고)일 수 있어 시간이 걸림 → 진행 메시지 표시
      setLoadMsg("공고를 불러오는 중… 이미지로 올린 공고는 OCR로 본문을 읽어 수십 초 걸릴 수 있어요.");
      try {
        const res = await extractJobPostingFromUrl(url.trim());
        setJd(res.text || "");
        const ocrUsed = res.extractor === "image_ocr"
          || (res.warnings || []).some(w => w.includes("OCR"));
        const cnt = res.char_count ?? (res.text || "").length;
        setJdStatus({
          tone: cnt >= 40 ? "good" : "warn",
          msg: ocrUsed
            ? `이미지 공고를 OCR로 읽었어요 · 실제 추출 ${cnt.toLocaleString()}자`
            : `공고 본문 추출 완료 · 실제 추출 ${cnt.toLocaleString()}자`,
        });
      } catch (e) {
        setJd("");
        setJdStatus({
          tone: "bad",
          msg: "공고를 불러오지 못했어요 · " + ((e as Error).message || "URL 확인 후 본문을 직접 붙여넣어 주세요"),
        });
      } finally {
        setLoading(false);
        setLoadMsg("");
      }
    } else if (jd.trim().length < 40) {
      setJdStatus({ tone: "warn", msg: "공고 본문이 짧습니다 · 핵심 요구사항이 누락될 수 있어요" });
    } else {
      setJdStatus({ tone: "good", msg: `공고 본문 확인 완료 · ${jd.trim().length.toLocaleString()}자` });
    }
  };

  return (
    <div className="card pad-card">
      <div className="card-head">
        <div className="icon-badge"><Ic.Doc size={19}/></div>
        <div>
          <h3>채용공고</h3>
          <p>지원하려는 공고를 붙여넣거나 URL로 불러오세요</p>
        </div>
      </div>
      <Seg value={tab} onChange={setTab} options={[{ v: "url", label: "URL" }, { v: "text", label: "텍스트 직접 입력" }]}/>
      {tab === "url" ? (
        <div className="field-row">
          <div className="input-wrap">
            <Ic.Link size={16}/>
            <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://… 채용공고 주소"
              onKeyDown={e => { if (e.key === "Enter") load(); }}/>
          </div>
        </div>
      ) : (
        <textarea className="ta" value={jd} onChange={e => { setJd(e.target.value); setJdStatus(null); }}
          placeholder="채용공고 본문을 붙여넣어 주세요 — 자격요건·우대사항이 있으면 더 정확해요"/>
      )}
      <div className="card-actions">
        <button className="btn dark sm" onClick={load} disabled={loading}>
          {loading ? <><Ic.Spinner size={15}/>불러오는 중…</> : <><Ic.Download size={15}/>공고 불러오기</>}
        </button>
        <button className="btn ghost sm" onClick={() => { setJd(""); setUrl(""); setJdStatus(null); setShowText(false); }}><Ic.Refresh size={14}/>초기화</button>
        {tab === "text" && <button className="link-btn" onClick={() => { setJd(SAMPLE_JD); setJdStatus({ tone: "good", msg: "예시 공고를 불러왔어요" }); }}>예시 공고</button>}
      </div>
      {loading && (
        <div className="status warn">
          <Ic.Spinner size={15}/>{loadMsg}
        </div>
      )}
      {!loading && jdStatus && (
        <div className={"status " + jdStatus.tone}>
          {jdStatus.tone === "good" ? <Ic.CheckCircle size={15}/> : <Ic.Alert size={15}/>}
          {jdStatus.msg}
        </div>
      )}
      {/* 추출한 공고 텍스트 실제로 보기 — URL 불러온 뒤 검증용 */}
      {!loading && tab === "url" && jd.trim().length > 0 && jdStatus?.tone !== "bad" && (
        <>
          <button className="link-btn" style={{ marginTop: 10 }} onClick={() => setShowText(v => !v)}>
            {showText ? "추출한 공고 텍스트 숨기기" : "추출한 공고 텍스트 보기"}
          </button>
          {showText && (
            <textarea className="ta" style={{ marginTop: 8 }} value={jd} readOnly
              onFocus={e => e.currentTarget.select()}/>
          )}
        </>
      )}
    </div>
  );
}

interface FileEntry { name: string; size: string; }
interface ApplicantCardProps {
  cl: string;
  setCl: (v: string) => void;
  files: FileEntry[];
  setFiles: (v: FileEntry[]) => void;
}
function ApplicantCard({ cl, setCl, files, setFiles }: ApplicantCardProps) {
  const [tab, setTab] = useState("text");
  const fileRef = useRef<HTMLInputElement>(null);
  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const next = [...files];
    Array.from(list).forEach(f => next.push({ name: f.name, size: Math.round(f.size / 1024) + "KB" }));
    setFiles(next);
  };
  return (
    <div className="card pad-card">
      <div className="card-head">
        <div className="icon-badge"><Ic.User size={19}/></div>
        <div>
          <h3>지원자 자료</h3>
          <p>자소서·이력서·포트폴리오를 입력하세요 · 여러 개 추가 가능</p>
        </div>
      </div>
      <Seg value={tab} onChange={setTab} options={[{ v: "text", label: "텍스트" }, { v: "file", label: "PDF · TXT 업로드" }]}/>
      {tab === "text" ? (
        <textarea className="ta tall" value={cl} onChange={e => setCl(e.target.value)}
          placeholder="자소서 / 이력서 / 포트폴리오 내용을 붙여넣어 주세요"/>
      ) : (
        <div className="drop" onClick={() => fileRef.current?.click()}
          onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); addFiles(e.dataTransfer.files); }}>
          <Ic.Upload size={22}/>
          <b>파일을 끌어다 놓거나 클릭해 업로드</b>
          <span>PDF · TXT · 최대 10MB</span>
          <input ref={fileRef} type="file" multiple hidden accept=".pdf,.txt"
            onChange={e => addFiles(e.target.files)}/>
        </div>
      )}
      {files.length > 0 && (
        <div className="file-list">
          {files.map((f, i) => (
            <div className="file-chip" key={i}>
              <Ic.File size={15}/>
              <span className="fn">{f.name}</span>
              <span className="fs">{f.size}</span>
              <button onClick={() => setFiles(files.filter((_, j) => j !== i))}><Ic.Trash size={14}/></button>
            </div>
          ))}
        </div>
      )}
      <div className="card-actions">
        {tab === "text"
          ? <button className="link-btn" onClick={() => setCl(SAMPLE_CL)}>예시 자소서</button>
          : <button className="btn ghost sm" onClick={() => fileRef.current?.click()}><Ic.Plus size={15}/>자료 추가</button>}
        {(cl || files.length > 0) && <button className="btn ghost sm" onClick={() => { setCl(""); setFiles([]); }}><Ic.Refresh size={14}/>초기화</button>}
      </div>
    </div>
  );
}

interface OptionGroupProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}
function OptionGroup({ label, value, onChange, options }: OptionGroupProps) {
  return (
    <div className="opt-group">
      <div className="opt-label">{label}</div>
      <div className="opt-pills">
        {options.map(o => (
          <button key={o} className={"opt-pill" + (value === o ? " on" : "")} onClick={() => onChange(o)}>{o}</button>
        ))}
      </div>
    </div>
  );
}

export interface FormState {
  jd: string;
  cl: string;
  files: FileEntry[];
  jdStatus: JdStatus | null;
  opts: { weeks: string; level: string; intensity: string };
}

interface OptionCardProps {
  opts: FormState["opts"];
  setOpts: (u: (o: FormState["opts"]) => FormState["opts"]) => void;
  canStart: boolean;
  onStart: () => void;
  onReset: () => void;
}
function OptionCard({ opts, setOpts, canStart, onStart, onReset }: OptionCardProps) {
  const set = (k: string, v: string) => setOpts(o => ({ ...o, [k]: v }));
  return (
    <div className="card pad-card opt-card">
      <div className="card-head">
        <div className="icon-badge lime"><Ic.Filter size={19}/></div>
        <div>
          <h3>분석 옵션</h3>
          <p>로드맵과 추천을 내 상황에 맞게 조정</p>
        </div>
      </div>
      <OptionGroup label="로드맵 기간" value={opts.weeks} onChange={v => set("weeks", v)} options={["2주", "4주", "8주", "12주"]}/>
      <OptionGroup label="현재 수준" value={opts.level} onChange={v => set("level", v)} options={["입문", "기초", "실무", "심화"]}/>
      <OptionGroup label="학습 강도" value={opts.intensity} onChange={v => set("intensity", v)} options={["가볍게", "보통", "집중"]}/>
      <div className="cta-wrap">
        <button className="btn lime block cta" disabled={!canStart} onClick={onStart}>
          <Ic.Spark size={17}/>분석 시작
        </button>
        {!canStart && <div className="cta-hint">채용공고와 지원자 자료를 모두 입력하면 시작할 수 있어요</div>}
        <button className="btn ghost block" onClick={onReset}><Ic.Refresh size={14}/>전체 초기화</button>
      </div>
    </div>
  );
}

interface InputViewProps {
  form: FormState;
  setForm: React.Dispatch<React.SetStateAction<FormState>>;
  onStart: () => void;
}
export function InputView({ form, setForm, onStart }: InputViewProps) {
  const canStart = form.jd.trim().length > 0 && (form.cl.trim().length > 0 || form.files.length > 0);
  const reset = () => setForm(f => ({ ...f, jd: "", cl: "", files: [], jdStatus: null }));
  return (
    <div className="input-grid fade-in">
      <div className="input-col">
        <JobCard jd={form.jd} setJd={v => setForm(f => ({ ...f, jd: v }))}
          jdStatus={form.jdStatus} setJdStatus={s => setForm(f => ({ ...f, jdStatus: s }))}/>
        <ApplicantCard cl={form.cl} setCl={v => setForm(f => ({ ...f, cl: v }))}
          files={form.files} setFiles={v => setForm(f => ({ ...f, files: v }))}/>
      </div>
      <div className="input-col side">
        <OptionCard opts={form.opts} setOpts={u => setForm(f => ({ ...f, opts: u(f.opts) }))}
          canStart={canStart} onStart={onStart} onReset={reset}/>
      </div>
    </div>
  );
}
