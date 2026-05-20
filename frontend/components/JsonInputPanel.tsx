type Props = {
  value: string;
  onChange: (value: string) => void;
  onLoadSample: () => void;
  onAnalyze: () => void;
  isLoading: boolean;
  error: string | null;
};

export function JsonInputPanel({
  value,
  onChange,
  onLoadSample,
  onAnalyze,
  isLoading,
  error
}: Props) {
  return (
    <aside className="input-rail" aria-label="C 결과 입력">
      <div className="rail-header">
        <p className="eyebrow">Input Contract</p>
        <h1>D Part RAG Demo</h1>
        <p>
          C 파트의 <code>skill_gaps</code> 결과를 넣으면 큐레이션된 학습자료 DB에서 추천 자료와
          로드맵을 생성합니다.
        </p>
      </div>
      <div className="button-row">
        <button type="button" className="secondary-button" onClick={onLoadSample} disabled={isLoading}>
          샘플 불러오기
        </button>
        <button type="button" className="primary-button" onClick={onAnalyze} disabled={isLoading}>
          {isLoading ? "분석 중" : "분석 실행"}
        </button>
      </div>
      <label className="json-label" htmlFor="json-input">
        C output JSON
      </label>
      <textarea
        id="json-input"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        spellCheck={false}
      />
      {error && <p className="error-text">{error}</p>}
      <div className="pipeline-note">
        <strong>RAG 범위</strong>
        <p>웹 전체 검색이 아니라 80개 학습자료 DB에서 검색하는 추천 RAG입니다.</p>
      </div>
    </aside>
  );
}

