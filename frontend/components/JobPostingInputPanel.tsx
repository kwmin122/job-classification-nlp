import type { JobInputMode } from "@/lib/types";

const extractorLabel = (extractor: string): string => {
  const labels: Record<string, string> = {
    jobkorea_rsc: "잡코리아 (구조화)",
    jobkorea_description: "잡코리아 (S3 본문)",
    jobkorea_playwright: "잡코리아 (동적 렌더링)",
    jobkorea_meta_only: "잡코리아 (메타데이터만)",
    playwright: "동적 렌더링",
    html_parser: "HTML 파싱",
  };
  return labels[extractor] ?? extractor;
};

type Props = {
  value: string;
  onChange: (value: string) => void;
  sourceMode: JobInputMode;
  onSourceModeChange: (value: JobInputMode) => void;
  url: string;
  onUrlChange: (value: string) => void;
  onExtractUrl: () => void;
  isExtracting: boolean;
  sourceName?: string;
  extractor?: string;
  warnings: string[];
  error: string | null;
};

const sourceModes: Array<{ value: JobInputMode; label: string }> = [
  { value: "text", label: "텍스트" },
  { value: "url", label: "URL" },
];

export function JobPostingInputPanel({
  value,
  onChange,
  sourceMode,
  onSourceModeChange,
  url,
  onUrlChange,
  onExtractUrl,
  isExtracting,
  sourceName,
  extractor,
  warnings,
  error,
}: Props) {
  return (
    <section className="input-card" aria-label="지원할 채용공고">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Target JD</p>
          <h2>지원할 채용공고</h2>
        </div>
        <span className="field-count">{value.trim().length.toLocaleString()}자</span>
      </div>
      <p className="field-help">주요업무, 자격요건, 우대사항이 포함될수록 부족 역량 판단이 정확해집니다.</p>
      <SourceTabs
        modes={sourceModes}
        selected={sourceMode}
        onSelect={(mode) => onSourceModeChange(mode as JobInputMode)}
      />

      {sourceMode === "url" ? (
        <div className="source-action">
          <input
            suppressHydrationWarning
            type="url"
            value={url}
            onChange={(event) => onUrlChange(event.target.value)}
            placeholder="https://www.jobkorea.co.kr/Recruit/GI_Read/..."
          />
          <button type="button" onClick={onExtractUrl} disabled={isExtracting || !url.trim()}>
            {isExtracting ? "불러오는 중" : "URL 불러오기"}
          </button>
        </div>
      ) : null}

      {sourceMode === "url" ? (
        <p className="field-help">잡코리아, 사람인, 원티드 등 채용공고 URL을 붙여넣으세요.</p>
      ) : null}

      <ExtractionStatus sourceName={sourceName} extractor={extractor} warnings={warnings} error={error} />
      <textarea
        suppressHydrationWarning
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="분석에 사용할 채용공고 텍스트를 입력하거나, URL/PDF/TXT에서 불러온 뒤 확인하세요."
        rows={10}
      />
    </section>
  );
}

function SourceTabs({
  modes,
  selected,
  onSelect,
}: {
  modes: Array<{ value: string; label: string }>;
  selected: string;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="source-tabs" aria-label="입력 방식">
      {modes.map((mode) => (
        <button
          key={mode.value}
          type="button"
          className={selected === mode.value ? "selected" : ""}
          onClick={() => onSelect(mode.value)}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}

function ExtractionStatus({
  sourceName,
  extractor,
  warnings,
  error,
}: {
  sourceName?: string;
  extractor?: string;
  warnings: string[];
  error: string | null;
}) {
  if (!sourceName && !extractor && !warnings.length && !error) return null;
  return (
    <div className={error ? "extraction-status error" : "extraction-status"}>
      {sourceName || extractor ? (
        <span>
          {sourceName ? sourceName : "텍스트"} {extractor ? `· ${extractorLabel(extractor)}` : ""}
        </span>
      ) : null}
      {warnings.map((warning) => (
        <span key={warning}>{warning}</span>
      ))}
      {error ? <span>{error}</span> : null}
    </div>
  );
}
