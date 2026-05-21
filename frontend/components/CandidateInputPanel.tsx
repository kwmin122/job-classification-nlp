type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function CandidateInputPanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="내 지원 자료">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Candidate Evidence</p>
          <h2>내 지원 자료</h2>
        </div>
        <span className="field-count">{value.trim().length.toLocaleString()}자</span>
      </div>
      <p className="field-help">자소서, 이력서 요약, 포트폴리오, README에서 기술 사용 근거를 붙여넣으세요.</p>
      <textarea
        suppressHydrationWarning
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="예: Spring Boot 기반 주문 API를 개발했고 MySQL 쿼리 최적화를 수행했습니다."
        rows={10}
      />
    </section>
  );
}
