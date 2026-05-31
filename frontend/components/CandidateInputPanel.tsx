import type { CandidateInputMode, CandidateMaterialDraft } from "@/lib/types";

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
  materials: CandidateMaterialDraft[];
  onMaterialChange: (id: string, patch: Partial<CandidateMaterialDraft>) => void;
  onAddMaterial: () => void;
  onRemoveMaterial: (id: string) => void;
  onFileChange: (id: string, file: File) => void;
};

const candidateModes: Array<{ value: CandidateInputMode; label: string }> = [
  { value: "text", label: "텍스트" },
  { value: "file", label: "PDF/TXT" },
];

const materialLabels = ["자소서", "이력서", "포트폴리오", "README", "기타"];

export function CandidateInputPanel({
  materials,
  onMaterialChange,
  onAddMaterial,
  onRemoveMaterial,
  onFileChange,
}: Props) {
  const totalLength = materials.reduce((sum, material) => sum + material.text.trim().length, 0);

  return (
    <section className="input-card" aria-label="내 지원 자료">
      <div className="section-heading">
        <h2>내 지원 자료</h2>
        <span className="field-count">{totalLength.toLocaleString()}자</span>
      </div>
      <p className="field-help">자소서, 이력서, 포트폴리오, README에서 기술 사용 근거를 붙여넣으세요.</p>
      <div className="material-list">
        {materials.map((material, index) => (
          <article key={material.id} className="material-block">
            <div className="material-toolbar">
              <select
                value={material.label}
                onChange={(event) => onMaterialChange(material.id, { label: event.target.value })}
                aria-label="자료 종류"
              >
                {materialLabels.map((label) => (
                  <option key={label} value={label}>
                    {label}
                  </option>
                ))}
              </select>
              <div className="source-tabs compact" aria-label="지원 자료 입력 방식">
                {candidateModes.map((mode) => (
                  <button
                    key={mode.value}
                    type="button"
                    className={material.sourceMode === mode.value ? "selected" : ""}
                    onClick={() => onMaterialChange(material.id, { sourceMode: mode.value })}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>
              {materials.length > 1 ? (
                <button type="button" className="ghost-action" onClick={() => onRemoveMaterial(material.id)}>
                  삭제
                </button>
              ) : null}
            </div>

            {material.sourceMode === "file" ? (
              <label className="file-drop">
                <span>{material.label} PDF/TXT 업로드</span>
                <input
                  type="file"
                  accept=".pdf,.txt,application/pdf,text/plain"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) onFileChange(material.id, file);
                    event.currentTarget.value = "";
                  }}
                />
              </label>
            ) : null}

            <ExtractionStatus
              sourceName={material.sourceName}
              extractor={material.extractor}
              warnings={material.warnings}
              error={material.error}
              isExtracting={material.isExtracting}
            />

            <textarea
              suppressHydrationWarning
              value={material.text}
              onChange={(event) => onMaterialChange(material.id, { text: event.target.value })}
              placeholder={
                index === 0
                  ? "예: Spring Boot 기반 주문 API를 개발했고 MySQL 쿼리 최적화를 수행했습니다."
                  : "추가 지원 자료를 입력하거나 파일에서 불러온 뒤 확인하세요."
              }
              rows={8}
            />
          </article>
        ))}
      </div>
      <button type="button" className="secondary-action" onClick={onAddMaterial}>
        지원 자료 추가
      </button>
    </section>
  );
}

function ExtractionStatus({
  sourceName,
  extractor,
  warnings,
  error,
  isExtracting,
}: {
  sourceName?: string;
  extractor?: string;
  warnings: string[];
  error: string | null;
  isExtracting: boolean;
}) {
  if (!sourceName && !extractor && !warnings.length && !error && !isExtracting) return null;
  return (
    <div className={error ? "extraction-status error" : "extraction-status"}>
      {isExtracting ? <span>파일에서 텍스트를 추출하는 중입니다.</span> : null}
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
