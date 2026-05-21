import type { RecommendResponse } from "@/lib/types";

type Props = {
  result: RecommendResponse | null;
};

export function SummaryStrip({ result }: Props) {
  const gapCount = result?.skill_recommendations.length ?? 0;
  const topSkill = result?.top_priority_skill ?? "대기 중";

  return (
    <section className="summary-strip" aria-label="분석 요약">
      <Metric label="추천 직무" value={result?.predicted_job ?? "분석 전"} />
      <Metric label="직무 적합도" value={result ? `${Math.round(result.fit_score)}점` : "--"} />
      <Metric label="보완할 역량" value={`${gapCount}개`} />
      <Metric label="먼저 할 일" value={topSkill} accent />
    </section>
  );
}

function Metric({
  label,
  value,
  accent = false
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className={accent ? "metric metric-accent" : "metric"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
