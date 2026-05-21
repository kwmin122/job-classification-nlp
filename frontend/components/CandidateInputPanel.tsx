type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function CandidateInputPanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="내 지원 자료">
      <div className="section-heading">
        <p className="eyebrow">Candidate Evidence</p>
        <h2>내 지원 자료</h2>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="자소서, 이력서 요약, 포트폴리오 설명, GitHub README 내용을 붙여넣으세요."
        rows={10}
      />
    </section>
  );
}
