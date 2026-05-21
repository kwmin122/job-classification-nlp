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
    <aside className="input-rail" aria-label="분석 데이터 입력">
      <div className="rail-header">
        <p className="eyebrow">분석 입력</p>
        <h1>채용 준비 데이터</h1>
        <p>
          직무 분석 결과를 넣으면 보완할 역량에 맞춰 학습 자료, 실행 순서, 리포트를 생성합니다.
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
        분석 데이터 JSON
      </label>
      <textarea
        id="json-input"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        spellCheck={false}
      />
      {error && <p className="error-text">{error}</p>}
      <div className="pipeline-note">
        <strong>분석 방법</strong>
        <p>공식 문서, 강의, 실습 자료를 선별한 로컬 DB에서 관련 자료를 검색합니다.</p>
      </div>
    </aside>
  );
}
