type Props = {
  report: string | null;
  formula: string | null;
  ragScope: string | null;
  retrievalMode: string | null;
  embeddingModel: string | null;
  chunkingStrategy: string | null;
};

export function ReportPanel({
  report,
  formula,
  ragScope,
  retrievalMode,
  embeddingModel,
  chunkingStrategy
}: Props) {
  if (!report) {
    return null;
  }

  return (
    <section className="panel report-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Generated Explanation</p>
          <h2>자연어 분석 리포트</h2>
        </div>
      </div>
      <pre>{report}</pre>
      <div className="formula-box">
        <strong>추천 점수 공식</strong>
        <code>{formula}</code>
        <div className="retrieval-meta">
          <span>검색 방식: {retrievalMode}</span>
          <span>임베딩 모델: {embeddingModel}</span>
          <span>청킹: {chunkingStrategy}</span>
        </div>
        <span>{ragScope}</span>
      </div>
    </section>
  );
}
