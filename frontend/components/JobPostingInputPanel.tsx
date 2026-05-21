type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function JobPostingInputPanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="지원할 채용공고">
      <div className="section-heading">
        <p className="eyebrow">Target JD</p>
        <h2>지원할 채용공고</h2>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="채용공고 본문을 붙여넣으세요. 예: 주요업무, 자격요건, 우대사항"
        rows={10}
      />
    </section>
  );
}
