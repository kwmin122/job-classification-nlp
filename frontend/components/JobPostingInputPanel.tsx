type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function JobPostingInputPanel({ value, onChange }: Props) {
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
      <textarea
        suppressHydrationWarning
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="예: 백엔드 개발자. Docker 기반 배포 경험 필수. AWS 운영 경험 우대."
        rows={10}
      />
    </section>
  );
}
