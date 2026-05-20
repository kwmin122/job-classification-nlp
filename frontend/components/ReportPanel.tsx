type Props = {
  report: string | null;
  formula: string | null;
  ragScope: string | null;
};

export function ReportPanel({ report, formula, ragScope }: Props) {
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
        <span>{ragScope}</span>
      </div>
    </section>
  );
}

